// SPDX-License-Identifier: Apache-2.0
package com.lightphone.parts;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

/** Restore the selected refresh rate's composition workaround after boot. */
public final class DisplayBootReceiver extends BroadcastReceiver {
    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        if (!Intent.ACTION_LOCKED_BOOT_COMPLETED.equals(action)
                && !Intent.ACTION_BOOT_COMPLETED.equals(action)) return;
        PendingResult pending = goAsync();
        restore(context, pending, 0);
    }

    private static void restore(Context context, PendingResult pending, int attempts) {
        if (DisplayComposition.applySavedRate(context)) {
            Log.i("LP3Display", "Restored display composition after boot");
            pending.finish();
        } else if (attempts < 3) {
            new Handler(Looper.getMainLooper()).postDelayed(
                    () -> restore(context, pending, attempts + 1), 1000);
        } else {
            Log.w("LP3Display", "Could not restore display composition after boot");
            pending.finish();
        }
    }
}
