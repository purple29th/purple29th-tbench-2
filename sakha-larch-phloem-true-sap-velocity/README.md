sakha larch phloem true sap velocity

Description

I am from Batagay in Sakha Republic near Verkhoyansk, coldest town, Evenk family herds reindeer near Yana river. My grandmother marks larch for resin and we cut thin phloem slabs zero point three mm and tag sap with fluorescein at one am in a heated yurt. Hamamatsu ORCA sCMOS photographs the glow but ice fog and lens point spread smear far beyond true streak. The rig writes SAPF with magic SAPF.

This task measures true sap flow velocity in mm per second for qualification. Simple level counting fails, generous level includes whole aureole and nearly doubles velocity, strict level loses thin tails that never reach full brightness and loses third to half. Background gain and scatter vary per slab and multiplier at offset forty scales final answer, hidden at ninety six uses one point two two, ignore and you fail by twenty two percent. Payload start varies forty eight sixty four eighty ninety six one twenty eight.

Energy preservation saves us. Optics do not create photons, only move them. So sum of background removed glow over streak plus faint skirt divided by true core level gives true count. Then area equals count times sx times sy, length equals area divided by zero point three zero mm vessel width, velocity equals length divided by zero point six zero seconds exposure times multiplier equals area times five point five five times multiplier mm per second.

A correct solver must handle data offset, multiplier, background bias, detector noise, and distinguish elongated phloem streaks that follow grain from compact bacterial autofluorescence plus far frost specks on yurt window. Some volumes have two distant streaks far apart that all count and must be summed, keeping only biggest fails forty to fifty percent.

Files

* /app/solve.py you write, last token is velocity in mm per second
* /app/data/scene.sapf sample nineteen mm per second example
* environment/Dockerfile installs pytest and copies sample
* solution/solve.py oracle reference
* tests/_gen.py generates sapf volumes
* tests/test_outputs.py secure verifier generating at runtime with random temp file names

Completion Rates

Each run is k equals five trials. Trial scores one only if all verifier cases pass.

Oracle three of three deterministic local harbor one point zero twelve of twelve pytest including ninety six one twenty eight plus random plus extra
Avocado zero to one of five measured by platform on submission due to multiplier plus multi component plus shape filter
Opus four of five due to halo recovery reasoning
GPT three of five

Model Analysis

Failure modes this task surfaces.

No background subtraction. Raw threshold without subtracting median background so halo plus background inflates forty to ninety percent over.

Fixed cutoff. Low threshold includes halo overcounts eighty to one thirty percent over, high threshold misses thin tails undercounts thirty to fifty percent under. No universal cutoff because brightness and blur vary.

No speck isolation. Keeps far frost specks far away overcounts six to twelve percent per speck.

No shape discrimination. Keeps compact round bacterial dots that are round, overcounts.

No halo growth. Stops at occupied region misses faint skirt energy undercounts fifteen to twenty five percent.

Hardcoded data offset sixty four fails heldout ninety six and one twenty eight which declare ninety six and one twenty eight.

Hardcoded multiplier one point zero fails hidden at ninety six gain one point two two fails twenty two percent low.

Anti Cheating Analysis

Hardcoded outputs impossible due to varied dims spacing amp bg sig noise seed object placement speck positions with random temp file names like input_a3f9.sapf. Sample nineteen vs hidden ranging eight to twenty five.

Modifying test files blocked, reward outside agent control written by tests/test.sh via python dash I dash S ctrf json parsing, secure runner audit hook blocks tests and b64decode and pathlib tricks.

Only correct conservation plus shape plus halo plus reading offset and multiplier passes.

Tags

Tags sakha larch phloem sap velocity Evenk Batagay Verkhoyansk halo recovery gain calibration payload offset human story oxidized sap flow
Author Tosin Daniel Jimoh purple29th at meta.com
