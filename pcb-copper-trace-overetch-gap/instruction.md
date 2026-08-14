Fix charge estimator in src/charge.py

Inspiration
This comes from battery coulomb counting where you integrate current to get charge despite baseline and spike artifacts. Blur spreads energy but conserves total, so true charge can be recovered from geometric occupancy. Similar to ultrasonic delam tasks.

Context
File to fix is src/charge.py function calculate_charge(samples, dt). Samples is list of current in mA length about 180 to 240, dt is seconds 0.5 0.8 1.0 or 2.0. Should return charge in mAh.

Trace generation is hidden in tests but roughly one main pulse. Flat core 45 to 60 samples occupancy 1.0, left feather 6 to 12 samples occupancy 0.3 times one minus normalized distance, right tail 16 to 22 samples occupancy 0.4 times one minus normalized distance. Amplitude amp few hundred mA. Baseline is constant offset bg plus Gaussian noise. Gaussian blur sigma a few points is applied to clean trace including spikes to simulate spreading, but it conserves sum.

Spikes are 1 to 3 narrow transients width a few samples amplitude about 0.9 times amp with triangular falloff. Spikes may appear far from pulse as isolated speck and must be ignored, or may overlap feather tail or even core and still must be excluded otherwise charge overcounts by a few percent. True charge is defined only from geometric occupancy sum true occ times amp times dt over 3600 and excludes spikes entirely. Tests compute truth at runtime from fixed random seeds, so no fixtures to read.

Bug
Current implementation estimates background as mean which is biased, uses fixed threshold 50, picks largest component by count not mass, uses max as plateau which is noise sensitive, and integrates as count times plateau times dt over 3600 with no tail inclusion and no spike suppression. It overcounts background and spikes and undercounts tails.

Expected
Fix the estimator to be robust without hardcoding positions gains or seeds. It should handle baseline that is not biased by pulse, handle noise, include thin feather and tail as part of true charge, exclude narrow spikes even when they overlap the pulse, and recover charge using conservation. Empty or all zero input should return near zero. Grading checks relative error within three percent. Tests include random seeds plus heavy spike case plus global fails where a spike sits in the tail plus threshold fails. Two guard tests ensure naive global mass and simple count threshold both fail. All tests must pass.

Verification
Run pytest tests/test_outputs.py dash v from repo root with PYTHONPATH set to include src.
