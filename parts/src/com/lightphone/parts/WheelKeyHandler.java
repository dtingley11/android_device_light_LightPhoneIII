// SPDX-License-Identifier: Apache-2.0
package com.lightphone.parts;

import android.app.ActivityManager;
import android.content.Context;
import android.graphics.Point;
import android.hardware.camera2.CameraAccessException;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.hardware.display.DisplayManager;
import android.hardware.input.InputManager;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.provider.Settings;
import android.util.Log;
import android.view.Display;
import android.view.InputDevice;
import android.view.KeyCharacterMap;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.ViewConfiguration;
import android.view.IWindowManager;
import android.view.WindowManagerGlobal;

import com.android.internal.os.DeviceKeyHandler;

/** Loaded by PhoneWindowManager; consumes only the built-in wheel's events. */
public final class WheelKeyHandler implements DeviceKeyHandler {
    private static final String TAG = "LP3Wheel";
    private final Context mContext;
    private final Handler mHandler = new Handler(Looper.getMainLooper());
    private final PowerManager mPower;
    private final WheelLockState mLockState;
    private final InputManager mInput;
    private final CameraManager mCamera;
    private final DisplayManager mDisplays;
    private final WheelButton mButton;
    private String mTorchCamera;
    private boolean mTorchEnabled;
    private int mButtonUser = -1;

    public WheelKeyHandler(Context context) {
        mContext = context;
        mPower = context.getSystemService(PowerManager.class);
        // The policy handler is created before TrustManager/NotificationManager.
        // KeyguardManager cannot be fetched safely from that early Context cache.
        mLockState = new WheelLockState(() -> {
            IWindowManager window = WindowManagerGlobal.getWindowManagerService();
            return window == null ? null : window::isKeyguardLocked;
        });
        mInput = context.getSystemService(InputManager.class);
        mCamera = context.getSystemService(CameraManager.class);
        mDisplays = context.getSystemService(DisplayManager.class);
        mButton = new WheelButton(new WheelButton.Scheduler() {
            public void postDelayed(Runnable task, long delay) { mHandler.postDelayed(task, delay); }
            public void remove(Runnable task) { mHandler.removeCallbacks(task); }
        }, ViewConfiguration.getLongPressTimeout(),
                () -> runAction(WheelActions.CLICK_SETTING, WheelActions.DEFAULT_CLICK),
                () -> runAction(WheelActions.HOLD_SETTING, WheelActions.DEFAULT_HOLD));
        try {
            mCamera.registerTorchCallback(new CameraManager.TorchCallback() {
                @Override
                public void onTorchModeChanged(String cameraId, boolean enabled) {
                    if (cameraId.equals(mTorchCamera)) mTorchEnabled = enabled;
                }
                @Override
                public void onTorchModeUnavailable(String cameraId) {
                    if (cameraId.equals(mTorchCamera)) mTorchEnabled = false;
                }
            }, mHandler);
        } catch (RuntimeException e) {
            Log.w(TAG, "Could not watch flashlight state", e);
        }
        mHandler.post(this::findTorchCamera);
    }

    @Override
    public KeyEvent handleKeyEvent(KeyEvent event) {
        InputDevice device = event.getDevice();
        if (device == null || device.isExternal()) return event;
        String name = device.getName();
        int scan = event.getScanCode();
        boolean rotation = "Pixart pat9126ja".equals(name) && (scan == 19 || scan == 20);
        boolean click = "gpio-keys".equals(name) && scan == 66;
        if (!rotation && !click) return event;
        if (Log.isLoggable(TAG, Log.DEBUG)) {
            Log.d(TAG, "Wheel input: scan=" + scan + " action=" + event.getAction());
        }
        int action = event.getAction();
        int repeat = event.getRepeatCount();
        long downTime = event.getDownTime();
        long eventTime = event.getEventTime();
        boolean canceled = event.isCanceled();
        mHandler.post(() -> {
            try {
                processKey(rotation, scan, action, repeat, downTime, eventTime, canceled);
            } catch (RuntimeException e) {
                mButton.cancel();
                Log.w(TAG, "Could not handle wheel input", e);
            }
        });
        return null;
    }

    private void processKey(boolean rotation, int scan, int action, int repeat,
                            long downTime, long eventTime, boolean canceled) {
        if (!mPower.isInteractive() || canceled) {
            mButton.cancel();
            return;
        }
        if (rotation) {
            // Turning while pressing the wheel must not also trigger its click action.
            mButton.cancel();
            if (action == KeyEvent.ACTION_DOWN && repeat == 0
                    && !mLockState.isLocked()) scroll(scan == 19 ? 1 : -1);
        } else if (action == KeyEvent.ACTION_DOWN) {
            if (repeat == 0) mButtonUser = ActivityManager.getCurrentUser();
            mButton.down(downTime, repeat);
        } else if (action == KeyEvent.ACTION_UP) {
            mButton.up(downTime, eventTime, canceled);
        }
    }

    private void scroll(int direction) {
        Display display = mDisplays.getDisplay(Display.DEFAULT_DISPLAY);
        if (display == null) return;
        int user = ActivityManager.getCurrentUser();
        if (Settings.System.getIntForUser(mContext.getContentResolver(),
                WheelActions.REVERSE_SETTING, 0, user) != 0) direction = -direction;
        Point size = new Point();
        display.getRealSize(size);
        MotionEvent.PointerProperties pointer = new MotionEvent.PointerProperties();
        pointer.id = 0;
        pointer.toolType = MotionEvent.TOOL_TYPE_MOUSE;
        MotionEvent.PointerCoords coords = new MotionEvent.PointerCoords();
        coords.x = size.x / 2f;
        coords.y = size.y / 2f;
        coords.setAxisValue(MotionEvent.AXIS_VSCROLL, direction);
        long now = SystemClock.uptimeMillis();
        MotionEvent motion = MotionEvent.obtain(now, now, MotionEvent.ACTION_SCROLL, 1,
                new MotionEvent.PointerProperties[]{pointer},
                new MotionEvent.PointerCoords[]{coords}, 0, 0, 1, 1,
                0, 0, InputDevice.SOURCE_MOUSE, 0);
        motion.setDisplayId(Display.DEFAULT_DISPLAY);
        try {
            if (!mInput.injectInputEvent(motion, InputManager.INJECT_INPUT_EVENT_MODE_ASYNC)) {
                Log.w(TAG, "Scroll event injection was rejected");
            }
        } finally {
            motion.recycle();
        }
    }

    private void runAction(String key, String fallback) {
        try {
            performAction(key, fallback);
        } catch (RuntimeException e) {
            Log.w(TAG, "Could not perform wheel action", e);
        }
    }

    private void performAction(String key, String fallback) {
        int user = ActivityManager.getCurrentUser();
        if (!mPower.isInteractive() || user != mButtonUser) return;
        String action = WheelActions.validated(Settings.System.getStringForUser(
                mContext.getContentResolver(), key, user), fallback);
        if ("flashlight".equals(action)) {
            toggleTorch();
            return;
        }
        if (mLockState.isLocked()) return;
        switch (action) {
            case "back": injectKey(KeyEvent.KEYCODE_BACK); break;
            case "home": injectKey(KeyEvent.KEYCODE_HOME); break;
            case "recents": injectKey(KeyEvent.KEYCODE_APP_SWITCH); break;
            case "play_pause": injectKey(KeyEvent.KEYCODE_MEDIA_PLAY_PAUSE); break;
            default: break;
        }
    }

    private void injectKey(int code) {
        long now = SystemClock.uptimeMillis();
        for (int action : new int[]{KeyEvent.ACTION_DOWN, KeyEvent.ACTION_UP}) {
            KeyEvent key = new KeyEvent(now, now, action, code, 0, 0,
                    KeyCharacterMap.VIRTUAL_KEYBOARD, 0, KeyEvent.FLAG_FROM_SYSTEM,
                    InputDevice.SOURCE_KEYBOARD);
            if (!mInput.injectInputEvent(key, InputManager.INJECT_INPUT_EVENT_MODE_ASYNC)) {
                Log.w(TAG, "Button action injection was rejected: " + code);
            }
        }
    }

    private void findTorchCamera() {
        if (mTorchCamera != null) return;
        try {
            for (String id : mCamera.getCameraIdList()) {
                CameraCharacteristics info = mCamera.getCameraCharacteristics(id);
                if (Boolean.TRUE.equals(info.get(CameraCharacteristics.FLASH_INFO_AVAILABLE))
                        && Integer.valueOf(CameraCharacteristics.LENS_FACING_BACK).equals(
                                info.get(CameraCharacteristics.LENS_FACING))) {
                    mTorchCamera = id;
                    return;
                }
            }
        } catch (CameraAccessException | RuntimeException e) {
            Log.w(TAG, "Could not find the rear flashlight", e);
        }
    }

    private void toggleTorch() {
        findTorchCamera();
        if (mTorchCamera == null) return;
        try {
            boolean enabled = !mTorchEnabled;
            mCamera.setTorchMode(mTorchCamera, enabled);
            mTorchEnabled = enabled;
        } catch (CameraAccessException | RuntimeException e) {
            Log.w(TAG, "Could not toggle the flashlight", e);
        }
    }
}
