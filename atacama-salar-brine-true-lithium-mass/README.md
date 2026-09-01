atacama salar brine true lithium mass

Description

I am Elena Lickanantay from Toconao on edge of Salar de Atacama in Chile. My family scraped salt since grandfather, now lithium pools for batteries. At one am we take glass slides to crust and tag brine with fluorescein, lithium carbonate needles glow under four eight eight nm and wind dust gets everywhere. Rig writes BRIN magic BRIN.

This task measures total lithium mass in milligrams. Simple level counting fails, generous includes whole salt aureole and nearly doubles mass, strict loses thin needle tails and loses third to half. Background gain and scatter vary per slide and multiplier at offset forty scales final mg hidden at ninety six uses one point two two.

Energy preservation saves us. Sum of background removed glow over needle plus faint skirt divided by true core level gives true count. Area equals count times sx times sy, thickness assumed zero point one five mm, density two point one one mg per mm3, mass equals area times thickness times density times multiplier equals area times zero point three one six five times multiplier mg.

Correct solver must handle data offset forty eight sixty four eighty ninety six one twenty eight, multiplier, background bias, noise, distinguish elongated brine needles along salt grain from compact halite dust plus far wind dust specks. Some volumes have two distant needle fields far apart must be summed.

Files

* /app/solve.py you write last token mg
* /app/data/scene.brin sample one point zero nine mg
* Dockerfile installs pytest copies sample
* solution/solve.py oracle
* _gen.py generates volumes
* test_outputs.py secure verifier random temp names

Completion Rates

Oracle three of three deterministic twelve of twelve pytest including ninety six one twenty eight
Avocado zero to one of five due to multiplier plus shape plus multi pool
Opus four of five
GPT three of five

Model Analysis

No background subtraction overcounts forty to ninety percent.

Fixed cutoff low includes halo eighty to one thirty percent over high misses tails thirty to fifty percent under.

No speck isolation overcounts six to twelve percent per far dust.

No shape filter keeps compact halite round overcounts.

No halo undercounts fifteen to twenty five percent.

Hardcoded offset sixty four fails ninety six one twenty eight.

Hardcoded multiplier one fails hidden twenty two percent.

Anti Cheating

Varied dims spacing amp bg sig noise seed placement random names input_c7d2.brin so hardcode fails. Secure runner blocks tests, reward via python I S ctrf.

Tags atacama salar brine lithium mass Lickanantay halite halo recovery payload offset

Author Tosin Daniel Jimoh purple29th at meta.com
