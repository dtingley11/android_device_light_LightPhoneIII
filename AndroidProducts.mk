# SPDX-License-Identifier: Apache-2.0
PRODUCT_MAKEFILES := \
    $(LOCAL_DIR)/lineage_LightPhoneIII.mk \
    $(LOCAL_DIR)/lineage_sdk_lp3_x86_64.mk

# Use breakfast LightPhoneIII to select the release configuration of the branch.
COMMON_LUNCH_CHOICES := \
    lineage_LightPhoneIII-bp4a-userdebug \
    lineage_sdk_lp3_x86_64-bp4a-userdebug
