# codimango/ink-blot-subvoxel-area

## Description

Paper mills check absorbency by letting a single ink droplet wick into a filter sheet. What you get is a `.inkb` file that stores a dark smear. The goal is to output the genuine fiber saturated area in mm2.

The picture is deceptive because capillary fibres plus cheap optics bleed darkness far outside the fibre wet region. The droplet looks like a large fuzzy ink cloud with delicate feathering that never hits full black after diffusion. Counting inky pixels above a cutoff fails for every batch because drop volume, sheet brightness, and pixel scale change per sheet.

A correct estimator cannot rely on pixel counts. It must untangle paper texture, far dust flecks, interior darkness, and the wispy tail that is only marginally darker than the sheet itself.

## Completion Rates

Sync'd at 72e84de: opus 2/5 40 percent, gpt 5.5 4/5 80 percent, avocado 1/5 20 percent, oracle 3/3 100 percent. Overall 7 of 15 non oracle passes. Main failure is counting dark pixels.

## Model Analysis

* Mill sheets are mostly bright paper with flat level plus camera grain. Lower percentile and robust spread give paper floor without blot influence.
* Isolated dark dots far away are dust, not ink. Keeping the blot with greatest total darkness via 8 neighbour BFS discards them.
* Darkest saturated value inside blot is never directly visible after wicking and sensor noise. Smoothing with small window and averaging a handful of darkest smoothed values gives stable reference.
* Light feathering around blot still belongs to droplet. Expanding region outward while edge ring stays darker than paper grain captures it.
* Physical size uses header pitch `sx*sy`. Fixed cutoffs miss, energy aware stays under 1 percent.

## Anti-Cheating Analysis

Example area differs from hidden ones, constant fails. Hidden images are built at evaluation time with random names in a temp folder, not reused. Execution is limited and disallowed library imports are rejected. Pure Python low level parsing required.

Author: Tosin Daniel Jimoh <purple29th@meta.com>
