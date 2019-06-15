#!/usr/bin/env python3
# vim:se fileencoding=utf-8 :
# (c) 2019 Michał Górny
# 2-clause BSD license

import argparse
import base64
import difflib
import hashlib
import json
import re
import subprocess
import sys


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
    argp.add_argument('-v', '--vote', required=True,
        type=argparse.FileType('r'),
        help='Path to your vote file')
    args = argp.parse_args(argv[1:])

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

    out = {'master_hash': sha512_file(args.master)}
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
