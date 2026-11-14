// SPDX-License-Identifier: Apache-2.0
package com.lightphone.parts;

import android.content.Context;
import android.hardware.display.DisplayManager;
import android.os.Handler;
import android.os.Looper;
import android.os.IBinder;
import android.os.Parcel;
import android.os.RemoteException;
import android.os.ServiceManager;
import android.provider.Settings;
import android.util.Log;
import android.view.Display;

/** Work around contrast instability in the LP3's high-refresh composition path. */
final class DisplayComposition {
    private static final String TAG = "LP3Display";
    private static final int FORCE_CLIENT_COMPOSITION = 1008;

    static boolean needsGpu(float rate) {
        return Float.isFinite(rate) && rate > 60.01f;
    }

    static boolean setForceGpu(boolean enabled) {
        IBinder flinger = ServiceManager.checkService("SurfaceFlinger");
        if (flinger == null) return false;
        Parcel data = Parcel.obtain();
        try {
            // The same signature-protected transaction used by Settings'
            // hardware-overlay control in this Android source revision.
            data.writeInterfaceToken(flinger.getInterfaceDescriptor());
            data.writeInt(enabled ? 1 : 0);
            return flinger.transact(FORCE_CLIENT_COMPOSITION, data, null, 0);
        } catch (RemoteException | RuntimeException e) {
            Log.w(TAG, "Could not update display composition", e);
            return false;
        } finally {
            data.recycle();
        }
    }

    static boolean applySavedRate(Context context) {
        return applySavedRate(context, 0);
    }

    private static boolean applySavedRate(Context context, int attempts) {
        DisplayManager manager = context.getSystemService(DisplayManager.class);
        Display display = manager == null ? null : manager.getDisplay(Display.DEFAULT_DISPLAY);
        if (display == null) return false;
        float peak = Settings.System.getFloat(context.getContentResolver(),
                Settings.System.PEAK_REFRESH_RATE, 60);
        float minimum = Settings.System.getFloat(context.getContentResolver(),
                Settings.System.MIN_REFRESH_RATE, 0);
        float requested = Math.max(validRate(peak), validRate(minimum));
        Display.Mode current = display.getMode();
        boolean force = false;
        for (Display.Mode mode : display.getSupportedModes()) {
            if (mode.getPhysicalWidth() == current.getPhysicalWidth()
                    && mode.getPhysicalHeight() == current.getPhysicalHeight()
                    && needsGpu(mode.getRefreshRate())
                    && mode.getRefreshRate() <= requested + 0.01f) {
                force = true;
                break;
            }
        }
        if (!force && needsGpu(current.getRefreshRate())) {
            // Keep the workaround until the asynchronous switch to 60 Hz has
            // completed, avoiding an unprotected high-refresh frame.
            if (attempts < 4) {
                Context application = context.getApplicationContext();
                new Handler(Looper.getMainLooper()).postDelayed(
                        () -> applySavedRate(application, attempts + 1), 250);
            }
            return setForceGpu(true);
        }
        return setForceGpu(force);
    }

    private static float validRate(float rate) {
        return Float.isFinite(rate) && rate > 0 ? rate : 0;
    }
}
