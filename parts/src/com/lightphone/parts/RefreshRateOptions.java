// SPDX-License-Identifier: Apache-2.0
package com.lightphone.parts;

import java.util.ArrayList;
import java.util.TreeSet;

/** Finite refresh-rate choices reported by the display driver. */
final class RefreshRateOptions {
    private static final float TOLERANCE = 0.01f;
    private final float[] rates;

    RefreshRateOptions(float[] supportedRates) {
        TreeSet<Float> sorted = new TreeSet<>();
        for (float rate : supportedRates) {
            if (Float.isFinite(rate) && rate > 0) sorted.add(rate);
        }
        ArrayList<Float> unique = new ArrayList<>();
        for (float rate : sorted) {
            if (unique.isEmpty() || rate - unique.get(unique.size() - 1) > TOLERANCE) {
                unique.add(rate);
            }
        }
        rates = new float[unique.size()];
        for (int i = 0; i < rates.length; i++) rates[i] = unique.get(i);
    }

    int size() { return rates.length; }
    float rateAt(int index) { return rates[index]; }
    String valueAt(int index) { return Float.toString(rates[index]); }

    int indexOf(float rate) {
        if (!Float.isFinite(rate) || rate <= 0) return -1;
        for (int i = 0; i < rates.length; i++) {
            if (Math.abs(rates[i] - rate) <= TOLERANCE) return i;
        }
        return -1;
    }

    int indexOf(String value) {
        if (value == null) return -1;
        try {
            return indexOf(Float.parseFloat(value));
        } catch (NumberFormatException ignored) {
            return -1;
        }
    }
}
