# codimango/seismic-p-wave-onset-pick

## Description

Agent writes stdlib-only Python at `/app/solve.py` that reads a seismic trace in custom SEIS binary (magic SEIS) and reports the P wave onset sample index. Each trace has one early P arrival plus a later larger S arrival plus short spike noise and variable dt and variable data offset. The script takes the trace path as first arg and prints the onset index as last token.

True onset is where P energy first rises from background. S is larger than P so max amplitude picks S and fails. Spike noise is up to 2x S but only 1 to 2 samples wide, so simple threshold picks spikes. Time windows must be converted to samples using dt read from header, so hardcoding sample counts fails when dt varies 0.001 vs 0.004. P near edge near 80 breaks background estimation if using whole trace median.

Correct method is energy ratio: estimate background from early quiet window without bias, estimate noise level robustly, compute rolling energy for short and long windows scaled by dt, look for sustained rise that stays above noise, then backtrack to first rise. Must handle larger S and short spikes.

## Completion Rates

Local 8 heldouts, expected calibration:
- oracle 8/8
- max amplitude shortcut fails 6/8 (picks S)
- fixed window shortcut fails 2/8 (dt variation)
- no background isolation fails near edge P at 80

## Model Analysis

Dominant failures will be picking max amplitude not STA LTA, using fixed sample windows not dt scaled, using whole trace median for background that includes S, and picking spike noise due to no sustain check.

## Anti-Cheating

Hardcoded indices blocked: 8 heldouts have P at 350,400,500,200,80,400,600,800 vs scene 300. Constant fails.
Data offset varies 64-128 and version varies 1/2, hardcoding 64 fails.
Dt varies 0.001,0.002,0.0025,0.004 so fixed sample windows fail.
Heavy spike and large S force STA LTA not amplitude.
Isolation: only trace.seis in agent container, hidden under tests/data mounted only at verify, copied to neutral temp name and solve.py copied into isolated temp dir. Generator not mounted, ground truth in ground_truth.json true P indices. Bans numpy scipy obspy etc via AST check.

Author: Tosin Daniel Jimoh
