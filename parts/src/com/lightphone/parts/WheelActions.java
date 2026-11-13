// SPDX-License-Identifier: Apache-2.0
package com.lightphone.parts;

final class WheelActions {
    static final String CLICK_SETTING = "lp3_wheel_click_action";
    static final String HOLD_SETTING = "lp3_wheel_hold_action";
    static final String REVERSE_SETTING = "lp3_wheel_reverse_scroll";
    static final String DEFAULT_CLICK = "back";
    static final String DEFAULT_HOLD = "flashlight";

    static boolean isValid(String action) {
        return "back".equals(action) || "home".equals(action) || "recents".equals(action)
                || "flashlight".equals(action) || "play_pause".equals(action)
                || "none".equals(action);
    }

    static String validated(String value, String fallback) {
        return isValid(value) ? value : fallback;
    }

    private WheelActions() {}
}
