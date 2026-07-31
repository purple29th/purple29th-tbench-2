I maintain cryo pumps used for high vacuum in our deposition tools. When a cryo pump goes through regeneration the cold head is warmed up and all the gas that was frozen on the array suddenly releases. The foreline gauge shows a big pressure burst that then decays. We log that burst as current from an ion gauge.

We need to know how much residual charge was in that main burst for contamination budgeting. The next lot cannot start if residual is too high.

Please create a file at /app/solve.py. It will be executed like python3 /app/solve.py /path/to/file.cryo and it should print the true burst charge in microcoulombs as the final token on stdout. We allow three percent error.

For development you have data/scene.cryo. The hidden evaluation uses completely different files that you have never seen. They have different total charge, different temperature drift, different gain, different pump vibration. Do not hardcode numbers from the sample.

File format CRYO is my own binary. All integers are little endian, floats are little endian too.

Bytes 0 to 3 is ASCII CRYO.
Bytes 4 to 5 is version as uint16, always 1.
Bytes 6 to 7 is flags as uint16, ignore.
Bytes 8 to 11 is number of samples N as uint32.
Bytes 12 to 15 is data offset as uint32, points to start of payload. Header can have padding 32 to 40 to up to 128, you must respect this field.
Bytes 16 to 23 is sample period as float64 seconds, example 0.0012.
Bytes 24 to 27 is gain as float32.
Bytes 28 to 31 is base pressure hint as float32, not reliable because cold head drift moves it.

Payload at data offset is N float32 values little endian. Each value is ion current in micro amps times 100. So to get micro amps divide by 100, then to get milliamps divide by 1000.

Inside each trace there is a slowly rising thermal baseline plus white noise plus one genuine gas burst. That burst is compact in time and has high total charge but it got smeared by the gauge low pass so its tails are wide and low. There are also a few isolated tiny spikes far away from valve clicks and one very wide low hump from the pump cart rolling. That hump has many samples so if you pick the footprint with most samples you will pick the wrong event. The correct event is the one with largest integrated mass.

Fixed thresholding does not work. With a low threshold you include the hump halo and the whole roll cart hump and you overcount by 70 to 100 percent. With a high threshold you cut off the smeared tails that still hold charge and you undercount by 30 to 60. No single threshold works across lots because gain and baseline drift change.

Charge is conserved through blur. The area under the smeared main burst equals the area of ideal rectangular burst before blur. So true charge can be recovered by integrating the background subtracted smeared signal over the main footprint plus its halo. For ideal rectangular burst, charge in microcoulombs equals number of ideal samples times plateau in micro amps divided by 1e6 times period times gain times 1e6? In our units payload is micro amps times 100, so convert to amps then integrate. Specifically charge uC equals sum of residual over main plus halo divided by 100 then divided by 1000 to get milliamps then divided by 1000 to get amps times period times gain times 1e6. Simplified as sum residual divided by 100 times period times gain. Check sample code.

Tolerances three percent.

Allowed imports are struct sys math random tempfile re collections only. Do not use numpy scipy skimage cv2 PIL Pillow networkx igraph imageio pandas torch tensorflow socket multiprocessing glob pathlib shutil io os pty importlib runpy ctypes. Do not use eval exec compile import chr. Do not use subprocess or os system popen exec fork walk listdir scandir open. Do not hide paths with chr bytes fromhex base64 b64decode bytearray tricks. Do not open or list tests folder and do not write test outputs heldout reference volume _gen geometric truth in your solver.

Return charge as last token.

Thanks for helping keep our chambers clean.
