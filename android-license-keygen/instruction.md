There's a compiled license checker at /app/validator.jar. Run it with a key and it prints ACCEPTED or REJECTED. Find a key it accepts and write it to /app/key.txt, one key on its own line. You can use 16 characters or the dashed form; dashes and spaces are ignored and case doesn't matter.

The checker reads from stdin if you don't pass an argument. You have java, javac, and javap on the box. Valid keys only use ABCDEFGHJKLMNPQRSTUVWXYZ23456789, so no I, O, 0, or 1. There are far too many to brute force, so you'll need to read the bytecode and figure out what it's actually checking for.
