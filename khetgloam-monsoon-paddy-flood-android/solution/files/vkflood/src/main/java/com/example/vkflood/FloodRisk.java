package com.example.vkflood;

/**
 * Khetgloam paddy terrace flood risk classifier for Kerala monsoon OUSB tablets.
 * Raw Vulkan backend, no Kompute. Bottom=terrace elevation, wall=bund/tree,
 * inlet=breach, exit=footpath to high ground. Risk 0 walls, 1..5 paddy cells.
 * Calibrated for paddy silt: 24 steps, 10 inject, alpha 0.25, inflow 2.8,
 * vel 12.0, wade 1.0/1.6 cost 2/4/6 — distinct from underground ref.
 */
public final class FloodRisk {
    static {
        System.loadLibrary("vkflood");
    }

    private FloodRisk() {}

    /**
     * Khetgloam paddy risk: per-cell 0..5 via GPU implicit diffusion (raw Vulkan),
     * Beffa FI, 3-band Dijkstra with paddy wading costs. Bottom/inlet/exit/wall
     * row-major float[] length rows*cols. Returns risk float[] same length.
     */
    public static native float[] floodRisk(
            float[] bottom, float[] wall, float[] inlet, float[] exit, int rows, int cols);
}
