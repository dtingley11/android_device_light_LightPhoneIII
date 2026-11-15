#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
set -e -o pipefail

lp3_device="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
lp3_source="$(cd -- "$lp3_device/../../.." && pwd -P)"
lp3_output="${OUT_DIR:-out}"
if [[ "$lp3_output" != /* ]]; then
    lp3_output="$lp3_source/$lp3_output"
fi
lp3_audio_hal="$lp3_output/target/product/LightPhoneIII/vendor/lib64/hw/audio.bluetooth_lp3.default.so"

cd "$lp3_source"
python3 "$lp3_device/tools/apply_source_patches.py"
if [[ -f "$lp3_audio_hal" ]]; then
    python3 "$lp3_device/tools/prepare_runtime_vendor.py" --audio-hal "$lp3_audio_hal"
else
    python3 "$lp3_device/tools/prepare_runtime_vendor.py" --bootstrap-audio
fi

source build/envsetup.sh
lunch lineage_LightPhoneIII-bp4a-userdebug
m -j8 audio.bluetooth_lp3.default
python3 "$lp3_device/tools/prepare_runtime_vendor.py" --audio-hal "$lp3_audio_hal"
if (( $# == 0 )); then
    set -- otapackage
fi
m -j8 "$@"
