hey so i am in android mobile config lab we dump config dependency files off device in custom binary. each config has signed exposure weight, positive adds exposure negative costs it. you choose which configs to turn on but rule if you turn on a config you must also turn on everything it depends on transitively, otherwise rollout invalid. empty rollout is valid with total 0 and size 0.

your job is write script to /app/solve.py that reads file path from first arg and prints one number as last token. we run like python3 /app/solve.py /app/data/scene.mcfg, sample file at /app/data/scene.mcfg you can test locally. hidden grading uses other mcfg files you never saw with different sizes dependency chains exposure values thresholds. dont hardcode sample.

goal is two steps but final print is second step only: first internally find largest total exposure any valid rollout can reach, call it max exposure. then among ALL valid rollouts that reach exactly that max exposure, find smallest number of configs turned on counting only non free. free riders never counted. the final number you print must be that minimal counted size, not the max exposure value. sample scene.mcfg answer 3 is minimal size.

custom twist exposure imbalance: header int32 reserved at offset 16 is threshold. configs with abs value below threshold are free riders. they are not counted in size and their own dependencies are ignored. but if a non free config depends on a free rider, that dependency is still enforced. for example file with threshold 6, config value 5 with dep dangling is free rider, not counted even if reachable.

watch out traps:
just adding up every positive is wrong because positive can drag in negative dependencies you cannot avoid.
turning on everything is also wrong because it pulls in avoidable costs.
some configs depend on each other in cycle so they must be activated as all or nothing.
a dependency id that names no config in file is dangling and ignored.
zero-gain padding must be excluded, for example config plus 30 that depends on minus 30 does not change total exposure, so it can be included without changing max, but minimal rollout must leave such pairs out.

binary format little endian all ints:
first four bytes ascii MCFG magic at offset zero
next four bytes u32 version at four
next four bytes u32 node count at eight
next four bytes u32 data offset at twelve
next four bytes int32 threshold at sixteen this is exposure imbalance threshold, configs with abs below threshold not counted and their own dependencies ignored, header is at least 64 bytes and data offset may be larger than 64 with zero padding so respect data offset dont hardcode 64
then node count records each has signed int32 id signed int32 value uint32 dep count then that many uint32 dep ids little endian. ids can be any int32 even negative, dep ids uint32 may encode negative via two complement, dep may be dangling.

parse it yourself from raw bytes with struct, no numpy scipy skimage cv2 PIL pillow networkx igraph imageio pandas torch tensorflow. also banned are os io pathlib shutil socket multiprocessing glob ctypes pty importlib runpy and subprocess os system popen exec and eval exec compile import and getattr setattr hasattr globals locals vars dir chr ord breakpoint base64 binascii codecs. use only stdlib struct sys collections deque. files may have up to about 3500 nodes, long 3500 chain forces iterative stack not recursive DFS so use iterative. chain length is up to 3500 not 2000.

run as python3 /app/solve.py path to mcfg and print final minimal size as last token.

grading exact int match on held outs, we recompute ground truth independently with different max flow impl edmonds karp vs dinic plus threshold counting with signed dep handling and free rider dep ignore, so hardcoded constant fails.
