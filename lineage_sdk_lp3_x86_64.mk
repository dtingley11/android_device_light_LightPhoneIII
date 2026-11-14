# SPDX-License-Identifier: Apache-2.0
# Keep Goldfish's board, kernel, vendor HALs and navigation configuration.
$(call inherit-product, vendor/lineage/build/target/product/lineage_sdk_phone_x86_64.mk)

PRODUCT_SOONG_NAMESPACES += device/light/LightPhoneIII
PRODUCT_PACKAGES += LP3Parts

PRODUCT_NAME := lineage_sdk_lp3_x86_64
PRODUCT_MODEL := LP3 development emulator

# Use an explicit path: LOCAL_PATH depends on the importing product.
PRODUCT_SDK_ADDON_SYS_IMG_SOURCE_PROP := vendor/lineage/build/target/product/source.properties
