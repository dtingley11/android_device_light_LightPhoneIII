# SPDX-License-Identifier: Apache-2.0
# Stock 1440 profile declarations lived in product and system_ext, which the
# Lineage build replaces. Android 16 leaves most profiles disabled if unset.
PRODUCT_PRODUCT_PROPERTIES += \
    bluetooth.profile.a2dp.source.enabled=true \
    bluetooth.profile.avrcp.target.enabled=true \
    bluetooth.profile.avrcp.controller.enabled=true \
    bluetooth.profile.hfp.ag.enabled=true \
    bluetooth.profile.asha.central.enabled=true \
    bluetooth.profile.gatt.enabled=true \
    bluetooth.profile.hid.host.enabled=true \
    bluetooth.profile.hid.device.enabled=true \
    bluetooth.profile.map.server.enabled=true \
    bluetooth.profile.opp.enabled=true \
    bluetooth.profile.pan.nap.enabled=true \
    bluetooth.profile.pan.panu.enabled=true \
    bluetooth.profile.pbap.server.enabled=true

PRODUCT_SYSTEM_EXT_PROPERTIES += \
    bluetooth.profile.sap.server.enabled=true

# The stock Qualcomm DSP offload path is incompatible with this Bluetooth stack.
PRODUCT_PRODUCT_PROPERTIES += ro.bluetooth.a2dp_offload.supported=false
