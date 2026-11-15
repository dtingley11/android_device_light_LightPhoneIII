#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Derive the LP3 vendor image with runtime compatibility fixes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from bluetooth_audio import module_path, policy_path, software_policy

from paths import DEVICE, HOST_BIN, SOURCE as ROOT
POLICIES = ('atfwd@2.0.policy', 'modemManager.policy', 'sensors-qesdk.policy',
            'wfdhdcphalservice.policy')
CONFIG = ROOT / 'device/light/LightPhoneIII/configs/runtime'
STOCK = ROOT / 'vendor/light/LightPhoneIII/proprietary/images/vendor.img'
OUTPUT = ROOT / 'vendor/light/LightPhoneIII/proprietary/runtime'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def run(args):
    env = dict(os.environ)
    env['PATH'] = str(HOST_BIN) + os.pathsep + env['PATH']
    p = subprocess.run(list(map(str, args)), text=True, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode:
        raise ValueError(f'{args[0]} failed ({p.returncode}): {p.stdout}\n{p.stderr}')
    return p.stdout


def debugfs(image, command, write=False):
    return run(['debugfs', *(['-w'] if write else []), '-R', command, image])


def quote(path):
    # debugfs parses quoted filenames; JSON escaping handles spaces and quotes.
    return json.dumps(str(path))


def extract(image, relative, destination):
    debugfs(image, f'dump {quote(relative)} {quote(destination)}')
    if not destination.is_file():
        raise ValueError(f'debugfs failed to extract {relative}')
    return destination.read_bytes()


def expected_changes(work, audio_hal=None):
    changes = {}
    for name in POLICIES:
        path = '/etc/seccomp_policy/' + name
        before = extract(STOCK, path, work / name)
        if re.search(rb'^gettid\s*:', before, re.M):
            raise ValueError(f'Unexpected preexisting gettid rule in {name}')
        changes[path] = (before, before + b'\n# Android 16 libc thread identity.\ngettid: 1\n')
    for relative, config, append in [
            ('/etc/msm_irqbalance.conf', 'msm_irqbalance.conf', False),
            ('/etc/selinux/vendor_sepolicy.cil', 'qmipriod.cil', True)]:
        before = extract(STOCK, relative, work / config)
        after = (before + b'\n' if append else b'') + (CONFIG / config).read_bytes()
        changes[relative] = (before, after)
    if audio_hal is not None:
        fragment = policy_path(ROOT).read_bytes()
        for sku in ('ravelin', 'ravelin_qssi'):
            path = f'/etc/audio/sku_{sku}/audio_policy_configuration.xml'
            before = extract(STOCK, path, work / (sku + '.xml'))
            changes[path] = (before, software_policy(before, fragment))
        path = '/lib64/hw/audio.bluetooth.default.so'
        before = extract(STOCK, path, work / 'stock-bluetooth-audio.so')
        changes[path] = (before, audio_hal.read_bytes())
    return changes


def file_context(relative):
    return 'u:object_r:vendor_file:s0' if relative.startswith('/lib64/') else 'u:object_r:vendor_configs_file:s0'


def inputs(audio_hal=None):
    profile = json.loads((ROOT / 'device/light/LightPhoneIII/configs/firmware-1440.json').read_text())
    expected = profile['partitions']['vendor']['sha256']
    if digest(STOCK) != expected:
        raise ValueError('Vendor input does not match verified stock firmware 1440')
    if audio_hal is not None:
        header = audio_hal.read_bytes()[:20]
        if len(header) < 20 or header[:6] != b'\x7fELF\x02\x01' or header[18:20] != b'\xb7\x00':
            raise ValueError('Expected an ARM64 Bluetooth audio shared library')
    return {'stock_sha256': expected, 'recipe_sha256': digest(Path(__file__)),
            'audio_recipe_sha256': digest(DEVICE / 'tools/bluetooth_audio.py'),
            'audio_hal_sha256': digest(audio_hal) if audio_hal is not None else None,
            'audio_policy_sha256': digest(policy_path(ROOT)) if audio_hal is not None else None,
            'configs': {p.name: digest(p) for p in sorted(CONFIG.iterdir()) if p.is_file()}}


def verify(image, manifest, work, audio_hal=None):
    if manifest['inputs'] != inputs(audio_hal) or digest(image) != manifest['sha256']:
        raise ValueError('Derived vendor image or recipe differs from its manifest')
    changes = expected_changes(work, audio_hal)
    for relative, (before, expected) in changes.items():
        record = manifest['files'][relative]
        actual = extract(image, relative, work / ('verified-' + Path(relative).name))
        if actual != expected or record != {
                'before_sha256': hashlib.sha256(before).hexdigest(),
                'after_sha256': hashlib.sha256(actual).hexdigest()}:
            raise ValueError(f'Unexpected derived vendor content: {relative}')
        info = debugfs(image, f'stat {quote(relative)}')
        if ('Mode:  0644' not in info or not re.search(r'User:\s+0\s+Group:\s+0', info)
                or file_context(relative) not in info):
            raise ValueError(f'Incorrect owner, mode or SELinux context: {relative}')
    if set(manifest['files']) != set(changes):
        raise ValueError('Unexpected file-change inventory')
    avb = HOST_BIN / 'avbtool'
    run([avb, 'verify_image', '--image', image])
    # Footer data is outside ext4; checking the full image is supported by e2fsck.
    run(['e2fsck', '-f', '-n', image])
    print(f'PASS: {len(changes)} vendor files, file labels, ext4 and AVB verified')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    audio = parser.add_mutually_exclusive_group()
    audio.add_argument('--audio-hal', type=Path, help='Built LP3 Bluetooth audio module')
    audio.add_argument('--bootstrap-audio', action='store_true',
                       help='Prepare the base vendor image before building the audio module')
    args = parser.parse_args()
    audio_hal = None if args.bootstrap_audio else (args.audio_hal or module_path(ROOT))
    recipe = inputs(audio_hal)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    image = OUTPUT / 'vendor.img'
    manifest_path = OUTPUT / 'manifest.json'
    if image.is_file() and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        if manifest.get('inputs') == recipe:
            with tempfile.TemporaryDirectory(prefix='verify-', dir=OUTPUT) as tmp:
                verify(image, manifest, Path(tmp), audio_hal)
            return
    if args.verify_only:
        raise ValueError('No verified runtime vendor image for this recipe')
    avb = HOST_BIN / 'avbtool'
    stock_info = run([avb, 'info_image', '--image', STOCK])
    original_size = int(re.search(r'Original image size:\s+(\d+)', stock_info)[1])
    salt = re.search(r'Salt:\s+(\w+)', stock_info)[1]
    with tempfile.TemporaryDirectory(prefix='prepare-', dir=OUTPUT) as tmp:
        work = Path(tmp)
        changes = expected_changes(work, audio_hal)
        derived = work / 'vendor.img'
        run(['cp', '--reflink=auto', '--sparse=always', STOCK, derived])
        run([avb, 'erase_footer', '--image', derived])
        if derived.stat().st_size != original_size:
            raise ValueError('Unexpected ext4 size after removing stock AVB footer')
        context = work / 'context'
        for index, (relative, (_, after)) in enumerate(changes.items()):
            context.write_bytes(file_context(relative).encode() + b'\0')
            replacement = work / f'file-{index}'
            replacement.write_bytes(after)
            debugfs(derived, f'rm {quote(relative)}', write=True)
            debugfs(derived, f'write {quote(replacement)} {quote(relative)}', write=True)
            for field, value in [('mode', '0100644'), ('uid', '0'), ('gid', '0'),
                                 ('atime', '0x495c0780'), ('ctime', '0x495c0780'),
                                 ('mtime', '0x495c0780'), ('crtime', '0x495c0780')]:
                debugfs(derived, f'set_inode_field {quote(relative)} {field} {value}', write=True)
            debugfs(derived, f'ea_set -f {quote(context)} {quote(relative)} security.selinux', write=True)
        # The enclosing development-signed vbmeta authenticates this descriptor.
        # Preserve the stock vendor fingerprint, patch level, salt, FEC and size.
        properties = re.findall(r"^\s*Prop:\s+(\S+) -> '([^']*)'\s*$", stock_info, re.M)
        if not properties:
            raise ValueError('Missing stock vendor AVB properties')
        prop_args = [arg for key, value in properties for arg in ('--prop', key + ':' + value)]
        run([avb, 'add_hashtree_footer', '--image', derived, '--partition_name', 'vendor',
             '--partition_size', str(STOCK.stat().st_size), '--hash_algorithm', 'sha256',
             '--salt', salt, *prop_args])
        manifest = {'version': 1, 'private_userdebug_only': True, 'inputs': recipe,
                    'sha256': digest(derived), 'bytes': derived.stat().st_size,
                    'files': {name: {'before_sha256': hashlib.sha256(before).hexdigest(),
                                     'after_sha256': hashlib.sha256(after).hexdigest()}
                              for name, (before, after) in changes.items()}}
        verify(derived, manifest, work, audio_hal)
        os.replace(derived, image)
        pending = OUTPUT / 'manifest.json.tmp'
        pending.write_text(json.dumps(manifest, indent=2) + '\n')
        os.replace(pending, manifest_path)
    print(f'Prepared private runtime vendor: {image}')


if __name__ == '__main__':
    main()
