// SPDX-License-Identifier: Apache-2.0
package com.lightphone.parts;

/** Main-thread click/hold state, independent of Android input dispatch. */
final class WheelButton {
    interface Scheduler {
        void postDelayed(Runnable callback, long delay);
        void remove(Runnable callback);
    }

    private final Scheduler mScheduler;
    private final long mHoldTimeout;
    private final Runnable mClick;
    private final Runnable mHold;
    private long mDownTime = -1;
    private boolean mHeld;
    private final Runnable mHoldCallback;

    WheelButton(Scheduler scheduler, long holdTimeout, Runnable click, Runnable hold) {
        mScheduler = scheduler;
        mHoldTimeout = holdTimeout;
        mClick = click;
        mHold = hold;
        mHoldCallback = () -> {
            if (mDownTime != -1 && !mHeld) {
                mHeld = true;
                mHold.run();
            }
        };
    }

    void down(long downTime, int repeat) {
        if (repeat != 0 || mDownTime == downTime) return;
        cancel();
        mDownTime = downTime;
        mScheduler.postDelayed(mHoldCallback, mHoldTimeout);
    }

    void up(long downTime, long eventTime, boolean canceled) {
        if (mDownTime != downTime) return;
        boolean held = mHeld;
        cancel();
        if (canceled || held) return;
        // Event timestamps preserve a hold even if the main looper was busy.
        if (eventTime - downTime >= mHoldTimeout) mHold.run();
        else mClick.run();
    }

    void cancel() {
        mScheduler.remove(mHoldCallback);
        mDownTime = -1;
        mHeld = false;
    }
}
