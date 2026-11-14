#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Install recovery's public ADB keys without following its product symlink."""
import argparse
import os
from pathlib import Path
import tempfile


def install(source, destination):
    public_keys = source.read_bytes()
    if not public_keys:
        raise ValueError('ADB public key file is empty')
    with tempfile.NamedTemporaryFile(prefix='.lp3-adb-keys-', dir=destination.parent,
                                     delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(public_keys)
    try:
        temporary.chmod(0o644)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    install(args.source, args.destination)


if __name__ == '__main__':
    main()
