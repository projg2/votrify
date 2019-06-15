#!/usr/bin/env python3
# vim:se fileencoding=utf-8 :
# (c) 2019 Michał Górny
# 2-clause BSD license

import argparse
import base64
import difflib
import hashlib
import json
import os.path
import re
import shutil
import subprocess
import sys
import tempfile


def confirmation_id(s):
    """
    Validate confirmation id.
    """
    if not re.match(r'[0-9a-fA-F]{4}', s):
        raise ValueError
    return s


def parse_vote(f):
    """
    Parse votes from a (submitted) ballot file.
    """

    for l in f:
        if l.startswith('#'):
            continue
        l = l.strip()
        if l:
            yield sorted(l.split())


CONF_RE = re.compile(r'-+ confirmation ([0-9a-f]{4}) -+')


def find_master_vote(f, confid):
    """
    Parse master ballot and find vote matching confid.
    """

    it = iter(f)
    # find correct confirmation id
    for l in it:
        m = CONF_RE.match(l)
        if m is not None:
            if m.group(1) == confid:
                break
    else:
        return

    # read votes
    for l in it:
        m = CONF_RE.match(l)
        if m is not None:
            return
        l = l.strip()
        if l:
            yield sorted(l.split())


def format_vote(v):
    for l in v:
        yield '  ' + ' '.join(l)


def run_countify(ballot, master, scripts):
    """
    Run countify to get election results.
    """

    with tempfile.TemporaryDirectory() as d:
        os.mkdir(os.path.join(d, 'x'))
        os.mkdir(os.path.join(d, 'results-x'))

        for x in ('countify', 'Votify.pm'):
            shutil.copyfile(os.path.join(scripts, x),
                            os.path.join(d, x))

        with open(os.path.join(d, 'x', 'ballot-x'), 'w') as f:
            shutil.copyfileobj(ballot, f)
        master.seek(0)
        with open(os.path.join(d, 'results-x', 'master-x'), 'w') as f:
            shutil.copyfileobj(master, f)

        s = subprocess.Popen(['perl', os.path.join(d, 'countify'),
                              '--rank', 'x'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             env={'HOME': d})
        sout, serr = s.communicate()
        if s.wait() != 0:
            raise SystemError('Countify failed with exit status {}, stderr:\n{}'
                    .format(s.wait(), serr.decode()))

        it = iter(sout.decode().splitlines())
        for l in it:
            if l == 'Final ranked list:':
                break
        else:
            raise SystemError('Final ranked list not found in countify output, stdout:\n{}'
                    .format(sout.decode()))
        for l in it:
            yield l.split()


def sha512_file(f):
    """
    Return SHA512 hash of data in the specified file.
    """
    h = hashlib.new('SHA512')
    h.update(f.read().encode())
    return base64.b64encode(h.digest()).decode()


def main(argv):
    argp = argparse.ArgumentParser(
        prog=argv[0],
        description='Verify your vote in master ballot and provide signed confirmation.')
    argp.add_argument('-b', '--ballot', required=True,
        type=argparse.FileType('r'),
        help='Election ballot file')
    argp.add_argument('-c', '--confirmation-id', required=True,
        type=confirmation_id,
        help='Your confirmation ID')
    argp.add_argument('-k', '--key-id',
        help='Key identifier for signing (passed to GnuPG)')
    argp.add_argument('-m', '--master', required=True,
        type=argparse.FileType('r'),
        help='Path to master ballot file')
    argp.add_argument('-o', '--output-file', default='-',
        type=argparse.FileType('wb'),
        help='File to write the result into (default: stdout)')
    argp.add_argument('-s', '--scripts',
        default=os.path.join(os.path.dirname(__file__), 'gentoo-elections'),
        help='Directory with votify script')
    argp.add_argument('-v', '--vote', required=True,
        type=argparse.FileType('r'),
        help='Path to your vote file')
    args = argp.parse_args(argv[1:])

    # verify your vote
    vote = list(parse_vote(args.vote))
    recorded_vote = list(find_master_vote(args.master,
                                          args.confirmation_id))

    if not recorded_vote:
        return 'No vote found for confirmation_id = {}'.format(
            args.confirmation_id)
    if vote != recorded_vote:
        return 'Vote mismatch found (old = your vote, new = vote recorded):\n{}'.format(
            '\n'.join(difflib.ndiff(
                [' '.join(x) for x in recorded_vote],
                [' '.join(x) for x in vote])))

    # compute election results
    try:
        results = list(run_countify(args.ballot, args.master, args.scripts))
    except SystemError as e:
        return e

    out = {
        'master_hash': sha512_file(args.master),
        'results': results,
    }
    j = json.dumps(out).encode()
    gpg_cmd = ['gpg', '--clearsign', '--comment',
        'This is a Votrify election vote confirmation']
    if args.key_id:
        gpg_cmd += ['--local-user', args.key_id]
    s = subprocess.Popen(gpg_cmd,
                         stdin=subprocess.PIPE,
                         stdout=args.output_file)
    s.communicate(j)
    if s.wait() != 0:
        return 'GnuPG failed with error {}'.format(s.wait())

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
