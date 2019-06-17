#!/usr/bin/env python3
# vim:se fileencoding=utf-8 :
# (c) 2019 Michał Górny
# 2-clause BSD license

import argparse
import email.utils
import json
import subprocess
import sys


class Color:
    bold = '\033[1m'
    red = '\033[31m'
    brown = '\033[33m'
    yellow = '\033[1;33m'
    green = '\033[1;32m'
    reset = '\033[0m'


def read_voters(f, domain):
    """
    Read voter list from file.  Append domain whenever full e-mail
    address is not being used.
    """
    for l in f:
        l = l.strip()
        if '@' not in l:
            l += '@' + domain
        yield l


def color_percentage(p):
    """
    Add ANSI colors to percentage.
    """
    if p < 0.25:
        c = Color.red
    elif p < 0.5:
        c = Color.brown
    elif p < 0.75:
        c = Color.yellow
    else:
        c = Color.green
    return '{}{:.2}%{}'.format(c, 100*p, Color.reset)


def main(argv):
    argp = argparse.ArgumentParser(
        prog=argv[0],
        description='Verify confirmations provided by voters.')
    argp.add_argument('-d', '--domain', default='gentoo.org',
        help='Domain to assume for voters without explicit e-mail address' +
             ' (default: gentoo.org)')
    argp.add_argument('-v', '--voters', required=True,
        type=argparse.FileType('r'),
        help='File containing eligible voter list')
    argp.add_argument(dest='confirmation', nargs='+',
        help='Paths to confirmation files')
    args = argp.parse_args(argv[1:])

    voters = list(read_voters(args.voters, args.domain))
    master_hash = set()
    results = set()
    voters_found = set()

    for path in args.confirmation:
        s = subprocess.Popen(['gpg', '--batch', '--logger-file', '/dev/null',
                              '--status-fd', '2', '--decrypt', path],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        sout, serr = s.communicate()
        if s.wait() != 0:
            return ('GnuPG failed on {} with exit status {}, status output:\n{}'
                    .format(path, s.wait(), serr))

        # find GOODSIG & VALIDSIG packets
        goodsig = None
        validsig = None
        for l in serr.decode().splitlines():
            if l.startswith('[GNUPG:] GOODSIG'):
                goodsig = l.split()[2]
            elif l.startswith('[GNUPG:] VALIDSIG'):
                validsig = l.split()[2]
        if goodsig is None or validsig is None:
            return ('GnuPG did not find good signature in {}, status output:\n{}'
                    .format(path, serr))
        # VALIDSIG should have full fingerprint
        if not validsig.endswith(goodsig):
            return ('GnuPG found mismatched signatures in {}, status output:\n{}'
                    .format(path, serr))

        # verify UID for key
        s = subprocess.Popen(['gpg', '--batch', '--with-colons',
                              '--list-key', validsig],
                             stdout=subprocess.PIPE)
        kout, _ = s.communicate()
        if s.wait() != 0:
            return 'GnuPG failed to list key {}, exit status: {}'.format(
                    validsig, s.wait())

        for l in kout.decode().splitlines():
            if l.startswith('uid:'):
                spl = l.split(':')
                # consider only fully valid UIDs
                if spl[1] in ['f', 'u']:
                    _, uid = email.utils.parseaddr(spl[9])
                    if uid in voters:
                        if uid in voters_found:
                            return ('Duplicate confirmation file {}, voter {}'
                                    .format(path, uid))
                        voters_found.add(uid)
                        break
        else:
            return 'No eligible voter found for file {}, key {}'.format(
                    path, validsig)

        # now finally process JSON
        j = json.loads(sout)
        master_hash.add(j['master_hash'])
        results.add(tuple(tuple(x) for x in j['results']))

    if len(master_hash) != 1:
        return 'Different ballot hashes in confirmations found:\n{}'.format(
                '\n'.join(master_hash))
    if len(results) != 1:
        return 'Different results in confirmations found:\n{}'.format(
                '\n---\n'.join(str(x) for x in results))

    print('Verified {}{}{} out of {}{}{} known voters.'
          .format(Color.bold, len(voters_found), Color.reset,
                  Color.bold, len(voters), Color.reset))
    print('The {} verified election results are:'
          .format(color_percentage(len(voters_found)/len(voters))))
    i = 0
    for x in next(iter(results)):
        if i + len(x) <= 7:
            # made it
            c = Color.green
        elif i >= 7:
            # didn't make it
            c = Color.brown
        else:
            # a problematic tie
            c = Color.yellow
        print('{}{}{}'.format(c, ' '.join(x), Color.reset))
        i += len(x)

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
