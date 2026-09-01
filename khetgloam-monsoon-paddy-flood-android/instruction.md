# Khetgloam Monsoon Paddy Flood Risk — Individual Human Story

I grew up in a khet — paddy terrace — village outside Alappuzha, Kerala. Every July monsoon, water comes down the Western Ghats, overtops the bunds, and my family's two-acre terrace goes from ankle to chest in an hour. My appa would wade through with a stick feeling the bund bottom, shouting which inlet breached. In 2018 we lost half the harvest because we didn't know which terrace would go under first and which bund exit was still walkable. Kids drowned trying to evacuate through deep cuts.

I left for engineering, but now I build for those farmers. No signal in the fields, only a $80 Android tablet sideloaded over OUSB (offline USB stick at the co-op). The tablet needs a reusable Android library that can score flood danger over the terrace grid in real time, without server, using the tablet's GPU via raw Vulkan compute. Kompute wrappers crash on our AOSP fork — we need pure Vulkan.

You must build from scratch in `/app` a library that does it. When you finish, `/app` must have:
* `libvkflood_host.so` — host x86-64 JNI library using raw Vulkan (so we can test on laptop with lavapipe)
* `risk.comp.spv` — SPIR-V compute shader
* `vkflood.aar` — Android AAR with `arm64-v8a` native library using raw Vulkan

## My village, my grid

I digitize each khet as a rectangular grid rows x cols. For each cell I have:
* `bottom` — bund bottom elevation metres (float32, row-major)
* `wall` — 1 if bund wall / raised bund / tree root that blocks water, else 0
* `inlet` — 1 where monsoon breaches the outer bund (inlet)
* `exit` — 1 where a footpath exits to high ground

All row-major length rows*cols.

I need per-cell risk 0..5 for the tablet to colour: 0 on walls, 1..5 risk on open paddy. Farmers see 5 = don't wade, leave now.

## Java API — what the tablet calls

Package `com.example.vkflood`:

```java
public final class FloodRisk {
    static { System.loadLibrary("vkflood"); }
    public static native float[] floodRisk(float[] bottom, float[] wall, float[] inlet, float[] exit, int rows, int cols);
}
```

JNI symbol follows standard naming `Java_com_example_vkflood_FloodRisk_floodRisk`. Inputs/outputs row-major.

## How my appa taught me water moves — the pipeline you must code

We use float32 everywhere. Constants you must use exactly (they came from our field calibration):

```
N_STEPS 20, N_INJECT 8, ALPHA 0.22, INFLOW 3.0, VEL_SCALE 10.0, WADE_LOW 1.2, WADE_HIGH 1.8, COST_SHALLOW 3, COST_MID 5, COST_DEEP 7
```

1. **GPU hydraulics — implicit storm pulse, raw Vulkan only.** Depth zero initially. First N_INJECT steps pin inlet depth at INFLOW as Dirichlet: surface level at inlet is bottom+INFLOW in every read, including stencil reads from neighboring free cells. Then release inlets to free.

   Each outer step evolves water surface eta = bottom + depth (never depth alone). Solve `(I - ALPHA * Laplacian) * eta_new = eta_old` with no-flux at walls and domain border, via Jacobi iteration to convergence on GPU. Right hand side stays the eta from start of step across inner sweeps. Each Jacobi refresh: `(start_eta + ALPHA*sum neighbor etas from prior sweep) / (1 + ALPHA*count open neighbors)`, walls/outside contribute 0 to sum and count. After convergence depth = max(eta_new - bottom,0), walls forced 0. Keep depth after every outer step, no in-place across outer steps. Workgroup 16x16, dispatch ceil(cols/16) x ceil(rows/16).

2. **Peak momentum — when danger is worst.** For each stored depth compute eta then speed from central differences of eta with self substitution at edges/walls, scaled by VEL_SCALE. Mean over free cells of depth*speed = momentum per step. Choose step with largest mean as assessment moment. Do not assume final step — monsoon pulse rises then decays, interior peak like my 2018 breach at step 12.

3. **Flood intensity — Beffa.** At chosen moment FI = depth * max(1, speed). Rank FI over free cells, split into 3 tertile groups using ceil division, no fixed thresholds. 1 low, 3 high.

4. **Evacuation difficulty — how hard to walk out.** Multi-source Dijkstra over free 4-grid from exits, walls blocked. Cost to enter neighbor = COST_SHALLOW if depth < WADE_LOW, COST_MID if between WADE_LOW inclusive and WADE_HIGH exclusive, COST_DEEP if >= WADE_HIGH. Tertile reachable costs same ceil into 1/2/3; unreachable free cells get 3; no exit case gives 3 everywhere. My appa's rule: knee below 1.2m you walk fast, chest 1.8m you crawl.

5. **Risk matrix.** For free cells risk = clamp(FI_level + difficulty -1, 1,5); walls 0.

## Environment — how I build offline over OUSB

Working dir `/app`. JDK 17, Gradle 8.7 offline cache pre-warmed, Android SDK with NDK 27.2.12479018 and CMake 3.22.1, Vulkan SDK with glslangValidator, Mesa lavapipe driver `VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.json`. No network at build or test time. Do NOT use Kompute — implement Vulkan instance, device, queues, buffers, descriptor sets, pipeline layout, compute pipeline, command buffers, fences yourself. Build Gradle Android library project from scratch and copy three artifacts to `/app` root.

I did this for my cousin's farm first: raw Vulkan host lib for laptop test, SPIR-V from `risk.comp`, arm64 AAR for tablet sideloaded via OUSB stick at co-op. No internet.

## Grading — how I know you saved my village

We drive same native lib across JNI on host software Vulkan (lavapipe) with random terrace layouts, bund walls, breach inlets, exits. Terrace sizes random, so no hardcoded. We also check AAR exists and contains arm64-v8a libvulkan-linked .so with JNI entry. Pipeline must match reference float tolerance with drift envelope 1e-2.

Build from scratch, no network, raw Vulkan only.

Author: Tosin Daniel Jimoh purple29th@meta.com — individualized human story for paddy farmers, Kerala Khet, monsoon flood + OUSB sideload.
