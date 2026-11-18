# SPDX-License-Identifier: Apache-2.0
DEVICE_PATH := device/light/LightPhoneIII
LP3_PREAUTHORIZE_ADB := false
-include $(DEVICE_PATH)/debug/adb-mode.mk

PRODUCT_SHIPPING_API_LEVEL := 33
PRODUCT_EXTRA_VNDK_VERSIONS := 32

PRODUCT_USE_DYNAMIC_PARTITIONS := true
AB_OTA_UPDATER := true
$(call inherit-product, $(SRC_TARGET_DIR)/product/virtual_ab_ota.mk)

# Firmware/bootloader/radio partitions are retained from the supported stock base.
AB_OTA_PARTITIONS += \
    boot \
    dtbo \
    recovery \
    vendor_boot \
    system \
    system_ext \
    product \
    vendor \
    odm \
    vendor_dlkm \
    vbmeta \
    vbmeta_system

PRODUCT_BUILD_VENDOR_BOOT_IMAGE := false
PRODUCT_BUILD_USERDATA_IMAGE := false
PRODUCT_BUILD_CACHE_IMAGE := false

PRODUCT_SOONG_NAMESPACES += $(DEVICE_PATH) vendor/light/LightPhoneIII
PRODUCT_PACKAGES += update_engine update_verifier fastbootd

PRODUCT_CHARACTERISTICS := nosdcard

$(call inherit-product, $(DEVICE_PATH)/bluetooth.mk)
$(call inherit-product, $(DEVICE_PATH)/ui.mk)

$(call inherit-product, vendor/light/LightPhoneIII/LightPhoneIII-vendor.mk)
$(call inherit-product, vendor/light/LightPhoneIII/telephony/telephony-vendor.mk)

# Private bring-up ADB authorization and log storage.
ifneq (,$(filter userdebug eng,$(TARGET_BUILD_VARIANT)))
PRODUCT_SYSTEM_PROPERTIES += ro.logd.kernel=true logd.size=4M
PRODUCT_PACKAGES_DEBUG += lp3-boot-log
ifeq ($(LP3_PREAUTHORIZE_ADB),true)
PRODUCT_ADB_KEYS := $(DEVICE_PATH)/debug/adb_keys
PRODUCT_PACKAGES_DEBUG += lp3-recovery-adb-keys
endif
endif

# Hardware power estimates must be compiled into framework resources.
DEVICE_PACKAGE_OVERLAYS += $(DEVICE_PATH)/power-overlay
PRODUCT_ENFORCE_RRO_EXCLUDED_OVERLAYS += $(DEVICE_PATH)/power-overlay

# LP3 physical controls: encoder scrolling, configurable wheel actions and Home.
DEVICE_PACKAGE_OVERLAYS += $(DEVICE_PATH)/overlay
PRODUCT_PACKAGES += LP3Parts
PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/configs/keylayout/gpio-keys.kl:$(TARGET_COPY_OUT_SYSTEM)/usr/keylayout/gpio-keys.kl \
    $(DEVICE_PATH)/configs/keylayout/Pixart_pat9126ja.kl:$(TARGET_COPY_OUT_SYSTEM)/usr/keylayout/Pixart_pat9126ja.kl

PRODUCT_COPY_FILES += \
    $(DEVICE_PATH)/configs/permissions/privapp-permissions-lp3-telephony.xml:$(TARGET_COPY_OUT_SYSTEM_EXT)/etc/permissions/privapp-permissions-lp3-telephony.xml
