#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Prepare the LP3's HIDL 2.0 software Bluetooth audio path."""
import os
from pathlib import Path
import re
import xml.etree.ElementTree as ET

A2DP_OUTPUTS = {
    'AUDIO_DEVICE_OUT_BLUETOOTH_A2DP',
    'AUDIO_DEVICE_OUT_BLUETOOTH_A2DP_HEADPHONES',
    'AUDIO_DEVICE_OUT_BLUETOOTH_A2DP_SPEAKER',
}


def module_path(root):
    output = Path(os.environ.get('OUT_DIR', 'out'))
    if not output.is_absolute():
        output = root / output
    return output / 'target/product/LightPhoneIII/vendor/lib64/hw/audio.bluetooth_lp3.default.so'


def policy_path(root):
    return root / 'frameworks/av/services/audiopolicy/config/bluetooth_audio_policy_configuration.xml'


def software_policy(before, fragment):
    text = before.decode('utf-8')
    original = ET.fromstring(before)
    primary = original.find('./modules/module[@name="primary"]')
    if primary is None:
        raise ValueError('Missing primary audio module')
    ports = {port.attrib['tagName'] for port in primary.findall('./devicePorts/devicePort')
             if port.get('type') in A2DP_OUTPUTS}
    if len(ports) != 3:
        raise ValueError('Expected three primary A2DP output ports')
    for name in sorted(ports):
        pattern = (r'^[ \t]*<devicePort\b[^>]*\btagName="' + re.escape(name)
                   + r'"[^>]*>.*?</devicePort>[^\S\n]*\n')
        text, count = re.subn(pattern, '', text, flags=re.M | re.S)
        if count != 1:
            raise ValueError('Unexpected A2DP device port: ' + name)
        pattern = (r'^[ \t]*<route\b[^>]*\bsink="' + re.escape(name)
                   + r'"[^>]*/>[^\S\n]*\n')
        text, count = re.subn(pattern, '', text, flags=re.M)
        if count != 1:
            raise ValueError('Unexpected A2DP route: ' + name)
    module = ET.fromstring(fragment)
    if module.tag != 'module' or module.get('name') != 'bluetooth' or module.get('halVersion') != '2.0':
        raise ValueError('Expected the HIDL 2.0 Bluetooth policy module')
    body = fragment.decode('utf-8').split('?>', 1)[-1].strip()
    body = '\n'.join('        ' + line for line in body.splitlines())
    pattern = (r'^[ \t]*<xi:include\s+href="/vendor/etc/'
               r'bluetooth_qti_hearing_aid_audio_policy_configuration.xml"\s*/>')
    text, count = re.subn(pattern, lambda _: body, text, flags=re.M)
    if count != 1:
        raise ValueError('Expected one vendor Bluetooth policy include')
    text = text.replace('Bluetooth Audio HAL for hearing aid',
                        'Bluetooth Audio HAL for A2DP and hearing aid')
    after = ET.fromstring(text)
    if len(after.findall('./modules/module[@name="bluetooth"]')) != 1:
        raise ValueError('Expected one standard Bluetooth audio module')
    if after.findall('./modules/module[@name="bluetooth_qti"]'):
        raise ValueError('Conflicting vendor Bluetooth audio module')
    return text.encode('utf-8')
