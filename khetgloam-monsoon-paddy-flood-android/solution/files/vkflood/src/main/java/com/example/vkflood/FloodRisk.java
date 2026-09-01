package com.example.vkflood;

/** Reusable GPU flood-risk classifier backed by a raw-Vulkan native lib. */
public final class FloodRisk {
    static {
        System.loadLibrary("vkflood");
    }

    private FloodRisk() {}

    /**
     * Classifies per-cell flood risk over an underground-space scenario (bottom
     * elevation, wall/room mask, inlet mask, exit mask) via GPU compute. Returns a
     * dense row-major grid of length rows*cols: risk level 1..5 per open cell, 0 on
     * walls.
     */
    public static native float[] floodRisk(
            float[] bottom, float[] wall, float[] inlet, float[] exit, int rows, int cols);
}
