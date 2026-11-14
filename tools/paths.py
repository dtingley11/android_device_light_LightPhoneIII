# SPDX-License-Identifier: Apache-2.0
"""Paths for a device tree checked out inside the Android source tree."""
import os
from pathlib import Path

DEVICE = Path(__file__).resolve().parents[1]
SOURCE = DEVICE.parents[2]
OUTPUT = Path(os.environ.get('OUT_DIR', 'out'))
if not OUTPUT.is_absolute():
    OUTPUT = SOURCE / OUTPUT
HOST_BIN = OUTPUT / 'host/linux-x86/bin'
