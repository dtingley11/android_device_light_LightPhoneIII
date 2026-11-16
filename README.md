# LineageOS for Light Phone III

LineageOS 23.2 / Android 16 sources for Light Phone III (TLP301), including LP3
controls, platform patches, and phone and x86-64 emulator targets.

## Setup

Use x86-64 Linux, a case-sensitive source directory without spaces, at least
400 GB of free space, and 64 GB of RAM. Install the
[Android build dependencies](https://source.android.com/docs/setup/start/requirements),
Repo, Git LFS, Python 3, `e2fsprogs`, and `lz4`.

```sh
mkdir -p ~/android/lp3
cd ~/android/lp3
repo init -u https://github.com/LineageOS/android.git -b lineage-23.2 \
  --git-lfs --no-clone-bundle
repo sync
git clone https://github.com/dtingley11/android_device_light_LightPhoneIII.git \
  device/light/LightPhoneIII
```

Run the following commands in Bash from this source directory.

## Phone

Extract the signed **00WW_1_440000** firmware into a local directory containing
`boot_b.img`, `vendor_boot_b.img`, `dtbo_b.img`, `vendor_b.img`, `odm_b.img`,
`vendor_dlkm_b.img`, `system_ext_b.img`, and `product_b.img`.
Proprietary firmware is not included in this repository.

First build the host tools using the generic emulator target, then prepare the
phone's firmware and apply its platform patches:

```sh
export OUT_DIR=out-lp3-phone
source build/envsetup.sh
lunch lineage_sdk_phone_x86_64-bp4a-userdebug
m -j8 avbtool fec lpunpack unpack_bootimg
export PATH="$ANDROID_HOST_OUT/bin:$PATH"

lp3_device=device/light/LightPhoneIII
lp3_firmware=/absolute/path/to/stock-1440
python3 "$lp3_device/tools/prepare_firmware.py" --images "$lp3_firmware" \
  --boot "$lp3_firmware/boot_b.img" \
  --vendor-boot "$lp3_firmware/vendor_boot_b.img" \
  --dtbo "$lp3_firmware/dtbo_b.img"
python3 "$lp3_device/tools/prepare_telephony.py" --images "$lp3_firmware"
bash "$lp3_device/tools/build.sh"
```

The OTA is written to
`out-lp3-phone/target/product/LightPhoneIII/lineage_LightPhoneIII-ota.zip`.
Firmware preparation is required once per fresh checkout. For subsequent
builds, set the same `OUT_DIR` and run
`bash device/light/LightPhoneIII/tools/build.sh` from the source directory.
Development builds use test keys and retain ADB authentication.

## Emulator

The emulator includes the LP3 controls app and uses Android's virtual hardware.
It does not require LP3 firmware. Hardware-specific behavior, including the
physical panel and wheel, requires the phone.

```sh
export OUT_DIR=out-lp3-emulator
source build/envsetup.sh
python3 device/light/LightPhoneIII/tools/apply_source_patches.py
git -C external/chromium-webview/prebuilt/x86_64 lfs install --local
git -C external/chromium-webview/prebuilt/x86_64 lfs pull --include=webview.apk --exclude=
lunch lineage_sdk_lp3_x86_64-bp4a-userdebug
m -j8
m -j8 emu_img_zip
emulator -no-snapshot -skin 1080x1240
```

Enable hardware virtualization and KVM access on the host. If graphics
initialization fails, add `-gpu swiftshader_indirect` to the emulator command.
The Android Studio image archive is written to
`out-lp3-emulator/target/product/emu64x/sdk-repo-linux-system-images.zip`.

## Credits

Auto-brightness configuration and camera-button settings issue fix adapted from [yarosz/lp3-treble](https://github.com/yarosz/lp3-treble).

Bootloader unlock method by [vandamd/light-guide](https://github.com/vandamd/light-guide).
