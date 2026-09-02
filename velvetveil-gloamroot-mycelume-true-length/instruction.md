hey - im tosin field myc in willamette. i map honey fungus armillaria ostoyae at HJ andrews forest. we call it velvetveil gloamroot cause it makes duff slab glow green at 1am foxfire. my folks are mushroom foragers, deer and boar dig where bloom next, so we need total active cord length per slab.

i image slabs with hamamatsu orca lowlight sCMOS on motor stage. no flash just 30sec exposure. rig writes custom file i made up called MYCR - mycelial cord radiance. sample at /app/data/scene.mycr about 13-15 mm length in sample but real eval uses random slabs you never see with random temp names like input_a3f9.mycr, random width height pitch base blur seed and calibration multiplier that changes per lot.

you must write /app/solve.py. we run python /app/solve.py /tmp/input_*.mycr and take last token as length mm.

MYCR layout my own, all little endian with embed fix:

Bytes 0 to 3 is ascii MYCR
Bytes 4 to 7 is u32 version =1
Bytes 8 to 11 is u32 dtype code 2=int16 16=float32
Bytes 12 to 15 is u32 width x voxels
Bytes 16 to 19 is u32 height y voxels
Bytes 20 to 23 is f32 sx mm per pixel x anisotropic file dependent must read changes per file
Bytes 24 to 27 is f32 sy mm per pixel y also anisotropic can be different from sx e.g. 0.11 vs 0.10
Bytes 28 to 31 is u32 payload_start where voxel block begins. can be 48,64,80,96,128 - dont hardcode 64, we have hidden lots at 96 and 128.
Bytes 40 to 43 is f32 post_veil_multiplier scaling mm result 0.85-1.35 sample 1.0 hidden lot at offset 96 uses 1.22 - ignore and you fail by 22%. payload_start >=48 so mult at 40 never overlaps payload.

padding between header and payload is zero. At payload_start you have width*height samples dtype, x fastest so linear = x + width*y.

Inside slab:

real foxfire rhizomorphs - ragged elongated cords along fallen fir grain, longer than wide, branching, thats signal. Some slabs have two distant cords e.g. top-left and bottom-right both count - keep only brightest loses 40-50pct in double. Elongated means bounding box long side at least ten and more than one point six times short side and long side at most thirty five, and mass at least zero point three five times biggest.

round bacterial colonies bacillus subtilis - compact almost circular photon blobs isotropic must skip, i call false foxlights.

far soil dust specks tiny bright dots in far corners like 5,5 and 75,75 from camera window dust, each adds 6-12pct if summed must skip and must not bridge to real cords during growing.

we use 8 neighbour connectivity 2D to group logically but strategy yours.

why naive fails:

low thresh includes whole aureole from fog plus PSF lens and doubles length. high thresh clips hyphal tails dim from partial fill loses third to half. no fixed number works cause duff base glow mult blur shifts per lot.

energy conserved - photons only spread optics dont create them. Total glow stays same. So length can be recovered via background subtracted glow total over core plateau brightness times sx sy divided by zero point four mm hyphal repeat times multiplier. Samples: background corrected total over plateau gives pixel count, times sx sy gives area, divided by 0.4 gives length, times multiplier. Challenge is estimating base and plateau robustly per slab without including dust or round colonies.

tolerance 3pct relative. simple thresholds 50-130pct off.

coding rules from scratch stdlib only.

parse bytes yourself. allowed struct sys math random tempfile re. forbidden numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath shutil ctypes importlib runpy. forbidden calls eval exec compile __import__. no tricks subprocess os.system popen exec fork walk listdir scandir rglob pty filesystem listing or hiding forbidden file names with chr fromhex base64 b64decode bytearray. dont open or list /tests dont mention test_outputs heldout _gen GEOM_TRUTH geometric_truth reference_mass reference_length ground_truth in solver. must work on any random temp path.

print length mm as last token e.g. 13.462. dont hardcode sample.

this is forest mycology task not element mg, unique name velvetveil gloamroot mycelume true length willamette foxfire.

author tosin purple29th - field work at andrews at 1am offline, human srsly.
