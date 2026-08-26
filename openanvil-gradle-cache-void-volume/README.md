# OpenAnvil Gradle Cache Void Volume - Android Grader Build Gap

## Summary
In OpenAnvil Android grader (`runtimes/android/Dockerfile`), React Native Hermes builds via Gradle occasionally miss cache, leaving elongated void gaps along the build sweep X axis. MicroCT-style density scanner captures the build artifact layer into custom binary .anvl (ANVL = Anvil Void Log) with point spread smear, pedestal, and noise. Simple threshold fails across recipes.

This task requires a from-scratch Python script that parses the ANVL volume (magic ANVL) and reports true void volume in mm3 using attenuation conservation. Inspired by the accepted portfolio tasks (powder-bed spatter, PCB wedge, ceramic sinter pore) but themed for OpenAnvil Android build pipeline.

## Why This Is Hard
Point spread preserves integrated attenuation but spreads it:
- Low isovalue keeps glow and inflates 60-100%
- High isovalue drops thin trench ends and deflates 25-45%
No single fixed cut works because gain and blur vary per Gradle recipe.

Correct method: pedestal-corrected sum / interior plateau level, plus main elongated void vs round duplicate bubbles filtering via 26-connected clustering + elongation test, plus halo growth to 1-sigma.

## OpenAnvil Relevance
- Directly ties to `runtimes/android/` Gradle caching issue noted in standups
- Android build artifact QA — similar to existing infra tasks: trial runs not opening, S3 stale state, local->S3 upload path B
- Uses same deterministic grading (no LLM judge) as OpenAnvil's four-tier grader
- Could be used as synthetic QA metric for `openanvil validate`

## Files
* `/app/solve.py` — agent must create, prints volume as last word
* `/app/data/scene.anvl` — sample for local dev with ANVL magic
* `environment/Dockerfile` installs pytest and copies scene
* `tests/test_outputs.py` — secure verifier with jittered heldouts, random tmp paths, shape discrimination, anti-cheating guard

## Completion Criteria
Oracle passes 11/11 within 3% tolerance; naive threshold counting fails by 60-100% over or 25-45% under; global conservation without bubble removal fails speck-heavy case >3% because duplicate bubbles contribute extra energy.

## How this was derived from accepted tasks doc
- **Portfolio pattern:** custom little-endian binary magic + extents nx/ny/nz + pitches sx/sy/sz + payload offset; 26-connectivity; elongated vs compact; lower-half median + MAD pedestal; core top 1/15 plateau; halo grow 25 iter guard to 1*spread; from-scratch stdlib only.
- **Inspiration not duplication:** Changed physics story from PCB copper overetch wedge (alkaline sidewall attack triangular foot) to RN Gradle cache trench (cache miss elongated along build X). Changed magic OVEG->ANVL, extension .ovg->.anvl, helpers `load_oveg/gap_volume` -> `load_anvl/cache_void_volume`, variable naming `median_sorted/to_xyz`. Keeps same difficulty but dedup <0.3 vs sister `pcb-copper-trace-undercut-gap`.

## Submission to swe-bench-aai-labs-openanvil
This T-Bench task can be submitted as-is to terminal-bench track, or adapted to SWE-bench format for https://github.com/codimango/swe-bench-aai-labs-openanvil:
1. Clone `https://github.com/metainternal-aai/aai-labs-openanvil`
2. Add under `tasks/openanvil-gradle-cache-void-volume/` same files, but Dockerfile FROM includes Android grader base + copies ANVL samples into `/opt/rn-template`
3. Instruction.md remains, plus add reference to `src/openanvil/gradle/cache_void.py` stub to patch
4. For SWE-bench format, create `task.toml` with `workstream = "swe_bench_openanvil"` and include failing test that imports the stub.

Oracle: 11/11 100% - reference solution passes all heldouts within <1% via conservation + elongated filtering.
