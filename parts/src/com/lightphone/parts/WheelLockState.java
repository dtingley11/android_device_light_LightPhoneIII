// SPDX-License-Identifier: Apache-2.0
package com.lightphone.parts;

/** Resolve lock state at event time; an unavailable service must not unlock navigation. */
final class WheelLockState {
    interface Service {
        boolean isLocked() throws Exception;
    }

    interface Lookup {
        Service get() throws Exception;
    }

    private final Lookup mLookup;

    WheelLockState(Lookup lookup) {
        mLookup = lookup;
    }

    boolean isLocked() {
        try {
            Service service = mLookup.get();
            return service == null || service.isLocked();
        } catch (Exception e) {
            return true;
        }
    }
}
