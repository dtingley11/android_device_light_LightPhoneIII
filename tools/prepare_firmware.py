#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Stage verified stock LP3 images for a LineageOS source checkout."""
import argparse
import gzip
import hashlib
import json
import re
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile

from paths import SOURCE as ROOT
PROFILE = ROOT / 'device/light/LightPhoneIII/configs/firmware-1440.json'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def verify(path, expected, padding=False):
    size = path.stat().st_size
    if size != expected['bytes'] and not (padding and size > expected['bytes']):
        raise ValueError(f'{path.name}: unexpected image size {size}')
    result = hashlib.sha256()
    with path.open('rb') as stream:
        remaining = expected['bytes']
        while remaining:
            block = stream.read(min(1024 * 1024, remaining))
            if not block:
                raise ValueError(f'{path.name}: truncated image')
            result.update(block)
            remaining -= len(block)
        if any(any(block) for block in iter(lambda: stream.read(1024 * 1024), b'')):
            raise ValueError(f'{path.name}: nonzero data after signed image')
    if result.hexdigest() != expected['sha256']:
        raise ValueError(f'{path.name}: does not match firmware 1440')


def cpio_file(fragment, wanted):
    data = fragment.read_bytes()
    if data.startswith(b'\x1f\x8b'):
        data = gzip.decompress(data)
    elif not data.startswith((b'070701', b'070702')):
        data = subprocess.run(['lz4', '-d', '-c', str(fragment)],
                              check=True, capture_output=True).stdout
    offset = 0
    found = None
    while offset + 110 <= len(data):
        header = data[offset:offset + 110]
        if header[:6] not in (b'070701', b'070702'):
            raise ValueError('Invalid vendor ramdisk CPIO header')
        fields = [int(header[n:n + 8], 16) for n in range(6, 110, 8)]
        mode, size, namesize = fields[1], fields[6], fields[11]
        start = offset + 110
        if not namesize or start + namesize > len(data):
            raise ValueError('Invalid CPIO name')
        name = data[start:start + namesize - 1].decode()
        start = (start + namesize + 3) & ~3
        if start + size > len(data):
            raise ValueError('Truncated CPIO entry')
        if name.removeprefix('./') == wanted:
            if found is not None or not stat.S_ISREG(mode):
                raise ValueError('Ambiguous first-stage fstab')
            found = data[start:start + size]
        offset = (start + size + 3) & ~3
        if name == 'TRAILER!!!':
            break
    if found is None:
        raise ValueError('Stock vendor ramdisk is missing the first-stage fstab')
    return found


def copy_image(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['cp', '--reflink=auto', '--sparse=always', str(source), str(destination)],
                   check=True)


def write_vintf_modules(stage, fragments):
    blueprint = ['// Generated from verified stock VINTF fragments.', 'soong_namespace {}', '']
    packages = ['# Stock HAL manifest modules for build-time compatibility inspection.']
    names = set()
    build_inputs = stage / 'proprietary/vintf/build'
    build_inputs.mkdir(parents=True, exist_ok=True)
    for path in sorted(fragments.glob('*.xml')):
        name = 'lp3_stock_manifest_' + re.sub(r'[^A-Za-z0-9_]', '_', path.name)
        if name in names:
            raise ValueError('VINTF module name collision')
        names.add(name)
        filename = 'lp3_stock_' + path.name
        shutil.copy2(path, build_inputs / filename)
        blueprint.extend(['vintf_fragment {', f'    name: "{name}",',
                          f'    src: "proprietary/vintf/build/{filename}",',
                          '    vendor: true,', '}', ''])
        packages.append(f'PRODUCT_PACKAGES += {name}')
    (stage / 'Android.bp').write_text('\n'.join(blueprint) + '\n')
    (stage / 'LightPhoneIII-vendor.mk').write_text('\n'.join(packages) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--images', type=Path, help='Directory containing *_b.img files')
    inputs.add_argument('--super', type=Path, help='Local raw super backup; slot b is extracted')
    parser.add_argument('--boot', required=True, type=Path)
    parser.add_argument('--vendor-boot', required=True, type=Path)
    parser.add_argument('--dtbo', required=True, type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'vendor/light/LightPhoneIII')
    args = parser.parse_args()
    profile = json.loads(PROFILE.read_text())
    output = args.output.resolve()
    if output.exists():
        parser.error('Output already exists; choose a fresh directory')
    # Check signed inputs before creating any staged build configuration.
    verify(args.boot, profile['partitions']['boot'])
    verify(args.vendor_boot, profile['partitions']['vendor_boot'])
    if args.dtbo.stat().st_size not in (profile['partitions']['dtbo']['bytes'],
                                      profile['physical_sizes']['dtbo']):
        raise ValueError('DTBO is neither the signed image nor the captured partition size')
    verify(args.dtbo, profile['partitions']['dtbo'], padding=True)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.lp3-stage-', dir=output.parent) as work:
        work = Path(work)
        images = args.images.resolve() if args.images else work / 'images'
        if args.super:
            images.mkdir()
            subprocess.run(['lpunpack', '--slot=1', '-p', 'vendor_b', '-p', 'odm_b',
                            '-p', 'vendor_dlkm_b', str(args.super.resolve()), str(images)], check=True)
        for name in ('vendor', 'odm', 'vendor_dlkm'):
            verify(images / f'{name}_b.img', profile['partitions'][name])
        unpacked = {}
        for name, image in (('boot', args.boot), ('vendor_boot', args.vendor_boot)):
            destination = work / name
            subprocess.run(['unpack_bootimg', '--boot_img', str(image.resolve()),
                            '--out', str(destination)], check=True, capture_output=True)
            unpacked[name] = destination
        fragment = unpacked['vendor_boot'] / 'vendor_ramdisk00'
        fstab = cpio_file(fragment, 'first_stage_ramdisk/fstab.default')
        if hashlib.sha256(fstab).hexdigest() != profile['fstab_sha256']:
            raise ValueError('Unexpected first-stage fstab')
        committed_fstab = ROOT / 'device/light/LightPhoneIII/rootdir/etc/fstab.default'
        if committed_fstab.read_bytes() != fstab:
            raise ValueError('Device-tree fstab differs from the verified stock fragment')
        stage = work / 'stage'
        private = stage / 'proprietary'
        private.mkdir(parents=True)
        copy_image(unpacked['boot'] / 'kernel', private / 'kernel')
        copy_image(unpacked['vendor_boot'] / 'dtb', private / 'dtbs/lp3.dtb')
        copy_image(fragment, private / 'vendor_ramdisk00')
        copy_image(args.vendor_boot, private / 'images/vendor_boot.img')
        # Ignore only proven zero partition padding, retaining the signed DTBO image.
        with args.dtbo.open('rb') as source, (private / 'dtbo.img').open('wb') as target:
            remaining = profile['partitions']['dtbo']['bytes']
            while remaining:
                block = source.read(min(1024 * 1024, remaining))
                if not block:
                    raise ValueError('DTBO was truncated during staging')
                target.write(block)
                remaining -= len(block)
        for name in ('vendor', 'odm', 'vendor_dlkm'):
            copy_image(images / f'{name}_b.img', private / f'images/{name}.img')
        fragments = private / 'vintf/manifest'
        fragments.parent.mkdir(parents=True)
        subprocess.run(['debugfs', '-R', f'rdump /etc/vintf/manifest {fragments.parent}',
                        str(images / 'vendor_b.img')], check=True, capture_output=True)
        actual = {path.name: digest(path) for path in fragments.glob('*.xml')}
        if actual != profile['vintf_fragments']:
            raise ValueError('Stock vendor VINTF fragment extraction is incomplete or mismatched')
        lines = ['# Generated by tools/prepare_firmware.py; firmware 00WW_1_440000.',
                 'LP3_PREBUILT_PATH := vendor/light/LightPhoneIII/proprietary']
        for name in ('vendor', 'odm', 'vendor_dlkm', 'vendor_boot'):
            lines.append(f'BOARD_PREBUILT_{name.upper()}IMAGE := $(LP3_PREBUILT_PATH)/images/{name}.img')
        (stage / 'BoardConfigVendor.mk').write_text('\n'.join(lines) + '\n')
        write_vintf_modules(stage, fragments)
        manifest = {str(path.relative_to(stage)): digest(path) for path in sorted(stage.rglob('*'))
                    if path.is_file() and not path.is_symlink()}
        (stage / 'firmware-manifest.json').write_text(json.dumps({
            'firmware': profile['firmware'], 'input_images_match_oem_payload': True,
            'fstab_preserved': True, 'files': manifest}, indent=2) + '\n')
        stage.rename(output)
    print(f'Staged verified firmware 1440: {output}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(f'Firmware preparation failed: {error}') from None
