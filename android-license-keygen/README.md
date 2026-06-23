# codimango/android-license-keygen

Reverse-engineer a compiled offline license-key validator (`/app/validator.jar`, source withheld) and recover an accepted key. No network; brute force is infeasible, so the agent must read the bytecode (e.g. `javap -c`) and invert the multi-constraint check.
