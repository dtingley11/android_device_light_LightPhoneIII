// SPDX-License-Identifier: Apache-2.0
package com.lightphone.parts;

import android.hardware.display.DisplayManager;
import android.os.Bundle;
import android.preference.ListPreference;
import android.preference.PreferenceActivity;
import android.preference.SwitchPreference;
import android.provider.Settings;
import android.view.Display;
import android.view.MenuItem;
import android.widget.Toast;

import java.text.NumberFormat;
import java.util.ArrayList;

@SuppressWarnings("deprecation")
public final class ControlsActivity extends PreferenceActivity {
    @Override
    public void onCreate(Bundle state) {
        super.onCreate(state);
        addPreferencesFromResource(R.xml.controls);
        if (getActionBar() != null) getActionBar().setDisplayHomeAsUpEnabled(true);
        setupAction(WheelActions.CLICK_SETTING, WheelActions.DEFAULT_CLICK);
        setupAction(WheelActions.HOLD_SETTING, WheelActions.DEFAULT_HOLD);
        SwitchPreference reverse = (SwitchPreference) findPreference(WheelActions.REVERSE_SETTING);
        reverse.setChecked(Settings.System.getInt(getContentResolver(),
                WheelActions.REVERSE_SETTING, 0) != 0);
        reverse.setOnPreferenceChangeListener((preference, value) ->
                Settings.System.putInt(getContentResolver(), WheelActions.REVERSE_SETTING,
                        (Boolean) value ? 1 : 0));
    }

    @Override
    protected void onResume() {
        super.onResume();
        setupRefreshRate();
        DisplayComposition.applySavedRate(this);
    }

    private void setupRefreshRate() {
        ListPreference preference = (ListPreference) findPreference(Settings.System.PEAK_REFRESH_RATE);
        Display display = getSystemService(DisplayManager.class).getDisplay(Display.DEFAULT_DISPLAY);
        ArrayList<Float> supported = new ArrayList<>();
        if (display != null) {
            Display.Mode current = display.getMode();
            for (Display.Mode mode : display.getSupportedModes()) {
                if (mode.getPhysicalWidth() == current.getPhysicalWidth()
                        && mode.getPhysicalHeight() == current.getPhysicalHeight()) {
                    supported.add(mode.getRefreshRate());
                }
            }
        }
        float[] rates = new float[supported.size()];
        for (int i = 0; i < rates.length; i++) rates[i] = supported.get(i);
        RefreshRateOptions options = new RefreshRateOptions(rates);
        preference.setEnabled(options.size() != 0);
        if (options.size() == 0) {
            preference.setSummary(R.string.refresh_rate_unavailable);
            return;
        }
        NumberFormat format = NumberFormat.getNumberInstance();
        format.setMaximumFractionDigits(2);
        CharSequence[] entries = new CharSequence[options.size()];
        CharSequence[] values = new CharSequence[options.size()];
        for (int i = 0; i < options.size(); i++) {
            entries[i] = getString(R.string.refresh_rate_hz, format.format(options.rateAt(i)));
            values[i] = options.valueAt(i);
        }
        preference.setEntries(entries);
        preference.setEntryValues(values);
        float fallback = getResources().getInteger(com.android.internal.R.integer.config_defaultPeakRefreshRate);
        float saved = Settings.System.getFloat(getContentResolver(),
                Settings.System.PEAK_REFRESH_RATE, fallback);
        int index = options.indexOf(saved);
        preference.setValue(index >= 0 ? options.valueAt(index) : null);
        if (index >= 0) {
            refreshRateSummary(preference, options.size());
        } else {
            preference.setSummary(Float.isFinite(saved) && saved > 0
                    ? getString(R.string.refresh_rate_hz, format.format(saved))
                    : getString(R.string.refresh_rate_no_limit));
        }
        preference.setOnPreferenceChangeListener((item, value) -> {
            int selected = options.indexOf((String) value);
            if (selected < 0) return false;
            float cap = options.rateAt(selected);
            if (DisplayComposition.needsGpu(cap) && !DisplayComposition.setForceGpu(true)) {
                showRefreshRateError();
                return false;
            }
            float oldMinimum = Settings.System.getFloat(getContentResolver(),
                    Settings.System.MIN_REFRESH_RATE, 0);
            if (!Settings.System.putFloat(getContentResolver(),
                    Settings.System.MIN_REFRESH_RATE, cap)) {
                DisplayComposition.applySavedRate(this);
                showRefreshRateError();
                return false;
            }
            if (!Settings.System.putFloat(getContentResolver(), Settings.System.PEAK_REFRESH_RATE, cap)) {
                Settings.System.putFloat(getContentResolver(),
                        Settings.System.MIN_REFRESH_RATE, oldMinimum);
                DisplayComposition.applySavedRate(this);
                showRefreshRateError();
                return false;
            }
            DisplayComposition.applySavedRate(this);
            preference.setValue(options.valueAt(selected));
            refreshRateSummary(preference, options.size());
            return true;
        });
    }

    private void refreshRateSummary(ListPreference preference, int count) {
        preference.setSummary(count == 1
                ? getString(R.string.refresh_rate_only_mode, preference.getEntry())
                : preference.getEntry());
    }

    private void showRefreshRateError() {
        Toast.makeText(this, R.string.refresh_rate_error, Toast.LENGTH_SHORT).show();
    }

    private void setupAction(String key, String fallback) {
        ListPreference preference = (ListPreference) findPreference(key);
        preference.setValue(WheelActions.validated(
                Settings.System.getString(getContentResolver(), key), fallback));
        preference.setSummary(preference.getEntry());
        preference.setOnPreferenceChangeListener((item, value) -> {
            String action = (String) value;
            if (!WheelActions.isValid(action)
                    || !Settings.System.putString(getContentResolver(), key, action)) return false;
            preference.setValue(action);
            preference.setSummary(preference.getEntry());
            return true;
        });
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == android.R.id.home) {
            finish();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }
}
