I am Kenji from Kyoto Japan, my grandfather runs bamboo charcoal kiln in Arashiyama forest with Moso bamboo. We cut bamboo at full moon and fire in土窯 at one am smoke is white then blue. After firing we take charcoal and image with iodine fluorescence that glows where iodine is adsorbed in bamboo pores, rig writes BMCH magic BMCH with variable payload start and multiplier. Need true adsorption capacity mg per g for water filter quality.

I need tool that tells total adsorption mg per g summing all elongated bamboo pores along grain that are real. Some charcoals have two distant pore fields both count.

Please make file at /app/solve.py last token mg per g.

Example at /app/data/scene.bmch inside container about fifteen mg per g. Hidden uses different charcoals with new sizes spacings brightness diffusion pitch random temp names like input_f6e3.bmch.

File layout bmch little endian.

Four bytes ascii BMCH.
Four bytes uint32 version.
Four bytes uint32 dtype two int16 sixteen float32.
Twelve bytes three uint32 nx ny nz.
Twelve bytes three float32 sx sy sz mm per voxel.
Four bytes uint32 data offset can be forty eight sixty four eighty ninety six one twenty eight.
Four bytes float32 multiplier at offset forty scales final mg per g sample one point zero hidden at ninety six is one point two two.

Inside each cube elongated bamboo pores along bamboo grain count. Compact ash inclusions round benign ignore. Tiny far kiln dust specks ignore.

Twenty six neighbour connectivity.

Calibration adsorption equals volume mm3 times two point four mg per g per mm3 times multiplier.

Naive brightness fails doubles or loses half. Energy preserved. Must handle background median dimmest noise MAD far dust interior plateau halo growth skipping dust.

Within three percent.

Coding rules only stdlib.

Print mg per g as last token.
