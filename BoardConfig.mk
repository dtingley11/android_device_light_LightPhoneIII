# SPDX-License-Identifier: Apache-2.0
DEVICE_PATH := device/light/LightPhoneIII
LP3_PREAUTHORIZE_ADB := false
-include $(DEVICE_PATH)/debug/adb-mode.mk
LP3_VENDOR_PATH := vendor/light/LightPhoneIII

# Generated only from verified LP3 firmware by tools/prepare_firmware.py.
include $(LP3_VENDOR_PATH)/BoardConfigVendor.mk

TARGET_ARCH := arm64
TARGET_ARCH_VARIANT := armv8-a
TARGET_CPU_ABI := arm64-v8a
TARGET_CPU_ABI2 :=
TARGET_CPU_VARIANT := generic
TARGET_2ND_ARCH := arm
TARGET_2ND_ARCH_VARIANT := armv8-a
TARGET_2ND_CPU_ABI := armeabi-v7a
TARGET_2ND_CPU_ABI2 := armeabi
TARGET_2ND_CPU_VARIANT := generic

TARGET_BOARD_PLATFORM := parrot
TARGET_BOOTLOADER_BOARD_NAME := LightPhoneIII
TARGET_NO_BOOTLOADER := true
BOARD_USES_QCOM_HARDWARE := true
BOARD_SHIPPING_API_LEVEL := 31
# Vendor policy 32.0 stays in prebuilt vendor; Android 16 selects platform policy.
include $(DEVICE_PATH)/sepolicy/SEPolicy.mk

# Stock 1440 GKI and its matching modules; no donor kernel or root patch.
TARGET_KERNEL_VERSION := 5.10
TARGET_PREBUILT_KERNEL := $(LP3_PREBUILT_PATH)/kernel
TARGET_FORCE_PREBUILT_KERNEL := true
BOARD_KERNEL_IMAGE_NAME := Image
BOARD_USES_GENERIC_KERNEL_IMAGE := true
BOARD_BOOT_HEADER_VERSION := 4
BOARD_KERNEL_PAGESIZE := 4096
BOARD_KERNEL_BASE := 0x00000000
BOARD_KERNEL_OFFSET := 0x00008000
BOARD_RAMDISK_OFFSET := 0x01000000
BOARD_KERNEL_TAGS_OFFSET := 0x00000100
BOARD_DTB_OFFSET := 0x01f00000
BOARD_KERNEL_CMDLINE := video=vfb:640x400,bpp=32,memsize=3072000 bootconfig
BOARD_BOOTCONFIG := androidboot.hardware=qcom androidboot.memcg=1 androidboot.usbcontroller=a600000.dwc3
BOARD_MKBOOTIMG_ARGS += --header_version $(BOARD_BOOT_HEADER_VERSION)
BOARD_MKBOOTIMG_ARGS += \
    --kernel_offset $(BOARD_KERNEL_OFFSET) \
    --ramdisk_offset $(BOARD_RAMDISK_OFFSET) \
    --tags_offset $(BOARD_KERNEL_TAGS_OFFSET) \
    --dtb_offset $(BOARD_DTB_OFFSET)
BOARD_RAMDISK_USE_LZ4 := true
BOARD_INCLUDE_DTB_IN_BOOTIMG := true
BOARD_PREBUILT_DTBIMAGE_DIR := $(LP3_PREBUILT_PATH)/dtbs
BOARD_PREBUILT_DTBOIMAGE := $(LP3_PREBUILT_PATH)/dtbo.img

# The OEM vendor_boot retains its DTB, first-stage fstab and early modules.

BOARD_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_VENDOR_BOOTIMAGE_PARTITION_SIZE := 100663296
BOARD_DTBOIMG_PARTITION_SIZE := 25165824
BOARD_RECOVERYIMAGE_PARTITION_SIZE := 104857600
BOARD_EXCLUDE_KERNEL_FROM_RECOVERY_IMAGE := true
BOARD_USES_RECOVERY_AS_BOOT := false
BOARD_MOVE_RECOVERY_RESOURCES_TO_VENDOR_BOOT := false
BOARD_INCLUDE_RECOVERY_RAMDISK_IN_VENDOR_BOOT := false

BOARD_SUPER_PARTITION_SIZE := 6442450944
BOARD_SUPER_PARTITION_GROUPS := qti_dynamic_partitions
BOARD_QTI_DYNAMIC_PARTITIONS_SIZE := 6438256640
BOARD_QTI_DYNAMIC_PARTITIONS_PARTITION_LIST := system system_ext product vendor odm vendor_dlkm
BOARD_FLASH_BLOCK_SIZE := 262144
BOARD_USES_METADATA_PARTITION := true
TARGET_USERIMAGES_USE_EXT4 := true
TARGET_USERIMAGES_USE_F2FS := true
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_SYSTEM_EXTIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_PRODUCTIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_ODMIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_VENDOR_DLKMIMAGE_FILE_SYSTEM_TYPE := ext4
TARGET_COPY_OUT_SYSTEM_EXT := system_ext
TARGET_COPY_OUT_PRODUCT := product
TARGET_COPY_OUT_VENDOR := vendor
TARGET_COPY_OUT_ODM := odm
TARGET_COPY_OUT_VENDOR_DLKM := vendor_dlkm

TARGET_RECOVERY_FSTAB := $(DEVICE_PATH)/rootdir/etc/fstab.default
TARGET_RECOVERY_PIXEL_FORMAT := RGBX_8888
TARGET_SCREEN_DENSITY := 320
TARGET_RECOVERY_UI_SCREEN_WIDTH := 1080
TARGET_RECOVERY_UI_SCREEN_HEIGHT := 1240

# The stock ravelin manifest and fragments also remain inside prebuilt vendor.
DEVICE_MANIFEST_SKUS := ravelin
DEVICE_MANIFEST_RAVELIN_FILES := $(DEVICE_PATH)/configs/vintf/manifest_ravelin.xml
DEVICE_MATRIX_FILE := $(DEVICE_PATH)/configs/vintf/compatibility_matrix.xml
DEVICE_FRAMEWORK_COMPATIBILITY_MATRIX_FILE += \
    hardware/qcom-caf/common/vendor_framework_compatibility_matrix.xml \
    $(DEVICE_PATH)/configs/vintf/framework_compatibility_matrix.xml

# Development signing uses the AOSP public test-key set. AVB stays enabled.
BOARD_AVB_ENABLE := true
BOARD_AVB_VBMETA_SYSTEM := system system_ext product
BOARD_AVB_VBMETA_SYSTEM_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_VBMETA_SYSTEM_ALGORITHM := SHA256_RSA4096
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_VBMETA_SYSTEM_ROLLBACK_INDEX_LOCATION := 2
BOARD_AVB_RECOVERY_KEY_PATH := external/avb/test/data/testkey_rsa4096.pem
BOARD_AVB_RECOVERY_ALGORITHM := SHA256_RSA4096
BOARD_AVB_RECOVERY_ROLLBACK_INDEX := $(PLATFORM_SECURITY_PATCH_TIMESTAMP)
BOARD_AVB_RECOVERY_ROLLBACK_INDEX_LOCATION := 1
TARGET_OTA_ASSERT_DEVICE := LightPhoneIII

# Private bring-up: bootstrap authenticated ADB before userdata/APEX activation.
ifneq (,$(filter userdebug eng,$(TARGET_BUILD_VARIANT)))
# GKI boot images use this command line; BOARD_KERNEL_CMDLINE belongs to vendor_boot.
GENERIC_KERNEL_CMDLINE += androidboot.apex.early_adbd=true androidboot.init_fatal_panic=true
ifeq ($(LP3_PREAUTHORIZE_ADB),true)
# Recovery has no product mount from which to load the normal /adb_keys link.
BOARD_RECOVERY_IMAGE_PREPARE = python3 ../tools/install_recovery_adb_keys.py $(TARGET_RECOVERY_ROOT_OUT)/lp3_adb_keys $(TARGET_RECOVERY_ROOT_OUT)/adb_keys
endif
endif

# Targeted userspace compatibility changes derived from verified stock vendor.
# The OEM vendor, kernel, modules and boot inputs remain available unchanged.
ifneq (,$(filter userdebug eng,$(TARGET_BUILD_VARIANT)))
BOARD_PREBUILT_VENDORIMAGE := $(LP3_PREBUILT_PATH)/runtime/vendor.img
endif
