# SPDX-License-Identifier: Apache-2.0
# Retain Qualcomm's platform exports used by the prebuilt vendor policy.
SYSTEM_EXT_PUBLIC_SEPOLICY_DIRS += \
    device/qcom/sepolicy/generic/public \
    $(DEVICE_PATH)/sepolicy/system_ext/public
SYSTEM_EXT_PRIVATE_SEPOLICY_DIRS += \
    device/qcom/sepolicy/generic/private \
    $(DEVICE_PATH)/sepolicy/system_ext/private
PRODUCT_PUBLIC_SEPOLICY_DIRS += device/qcom/sepolicy/generic/product/public
PRODUCT_PRIVATE_SEPOLICY_DIRS += device/qcom/sepolicy/generic/product/private

BOARD_SYSTEM_EXT_SEPOLICY_PREBUILT_DIRS += \
    device/qcom/sepolicy/generic \
    $(DEVICE_PATH)/sepolicy/system_ext
BOARD_PRODUCT_SEPOLICY_PREBUILT_DIRS += device/qcom/sepolicy/generic/product
