#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Apply the reviewed LP3 source patches, preserving unrelated local edits."""
import json
from pathlib import Path
import subprocess

from paths import DEVICE, SOURCE as ROOT


def main():
    for item in json.loads((DEVICE / 'patches/series.json').read_text()):
        project = ROOT / item['project']
        patch = DEVICE / 'patches' / item['patch']
        command = ['git', '-C', str(project), 'apply']
        if subprocess.run(command + ['--reverse', '--check', str(patch)],
                          capture_output=True).returncode == 0:
            print(f'{item["project"]}: LP3 patch already applied')
            continue
        subprocess.run(command + ['--check', str(patch)], check=True)
        subprocess.run(command + [str(patch)], check=True)
        print(f'{item["project"]}: applied {item["patch"]}')


if __name__ == '__main__':
    main()
