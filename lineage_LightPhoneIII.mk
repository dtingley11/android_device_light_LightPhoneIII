# SPDX-License-Identifier: Apache-2.0
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base_telephony.mk)
$(call inherit-product, vendor/lineage/config/common_full_phone.mk)
$(call inherit-product, device/light/LightPhoneIII/device.mk)

PRODUCT_NAME := lineage_LightPhoneIII
PRODUCT_DEVICE := LightPhoneIII
PRODUCT_BRAND := Light
PRODUCT_MODEL := TLP301
PRODUCT_MANUFACTURER := Light

# Keep private bring-up builds debuggable while retaining ADB authentication.
# This boolean is true for any nonempty value, including the string "false".
ifneq (,$(filter userdebug eng,$(TARGET_BUILD_VARIANT)))
PRODUCT_NOT_DEBUGGABLE_IN_USERDEBUG :=
# Bootstrap APEX activation cannot use /data to decompress an APEX.
PRODUCT_COMPRESSED_APEX := false
endif
