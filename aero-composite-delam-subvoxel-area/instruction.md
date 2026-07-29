hey i am in aero composites shop checking carbon fiber wing skins for delamination with ultrasonic pulse echo. we put probe on panel and delam reflects and shows up as bright echo but fiber weave plus beam spread smears it everywhere so photo looks like big fuzzy bright cloud not true tiny delaminated patch we need for strength grading.

i need program that tells true physical delaminated area in square mm not the smeared cloud. precision matters because thin feathered cracks matter for fatigue.

make file named solve dot py inside app folder. we call it as python app solve py with scan path as argument. last word printed taken as area.

you get one example to try named scene dot udel inside data folder that is inside app. hidden grading uses other files you never saw with different sizes spacings brightness delam shapes pitch. do not hardcode numbers from example.

what is udel. our own small binary for ultrasonic delam area. everything little endian.

file starts with four ascii U D E L.

version is next four bytes unsigned thirty two little endian.

dtype code next four bytes unsigned thirty two little endian. two means int16 pixels. sixteen means float32 pixels.

next eight bytes are two unsigned counts of pixels per axis width height nx ny.

next eight bytes are two float32 values mm per pixel per axis sx sy. they change every file so read them.

next four bytes unsigned data offset where pixels start.

after offset you have nx times ny values in announced dtype. x fastest so index for x y is x plus nx times y.

inside is one solid delamination region where echo is strong. center is flat and saturated bright where reflection saturates border is dimmer with partial fill smeared by beam spread and fiber scattering. flat background plus sensor noise. some scans have one or two tiny bright specks far away from fiber dust or resin pockets that must be ignored. keep only main connected bright mass using eight neighbours connectivity.

threshold counting cannot be precise. low cutoff includes huge halo and overcounts by eighty to one hundred twenty percent. high cutoff misses thin feathered cracks that never get bright enough and undercounts by thirty to fifty percent. no fixed cutoff works across files because gain and diffusion width change. the blurry images give best clue where echo is most concentrated not how many bright pixels there are. true core is flat but hidden by diffusion noise.

blur spreads energy but does not create or destroy echo. that physics makes precise area recovery possible despite smear but using it requires separating main delam from far specks estimating background without bias from delam itself estimating true concentrated echo level without being fooled by noise and deciding how far faint halo extends without merging specks. that is hard part.

simple shortcuts are off by large margin. grading is at three percent tolerance only genuine precise method passes.

implementation constraints parse bytes yourself using only standard library. allowed stdlib modules include struct sys math random tempfile re collections. banned libraries will be rejected by test from scratch are numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib os io posixpath ntpath genericpath. banned calls include eval exec compile __import__ chr. banned runtime tricks include subprocess os dot system popen exec fork walk listdir scandir open pty importlib runpy ctypes filesystem listing and any obfuscation that hides paths using chr bytes dot fromhex base64 b64decode bytearray. do not attempt to open or list the tests directory and do not reference test_outputs heldout reference area _gen GEOM_TRUTH geometric_truth in your solver source. your solver must work on random temporary files not hardcoded paths.

print area mm2 as last word on stdout.
