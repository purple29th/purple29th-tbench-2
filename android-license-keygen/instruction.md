# Recover a working license key

There's a compiled license checker at `/app/validator.jar`. You give it a license key and it tells you whether the key is good: it prints `ACCEPTED` for a valid key and `REJECTED` for anything else. You don't get the source, just the jar.

Try it like this:

  java -jar /app/validator.jar SOME-KEY-HERE

If you don't pass a key as an argument it reads one from stdin instead. Example:

  java -jar /app/validator.jar ABCD-EFGH-JKLM-NPQR

# What to do

Find a key the validator accepts and write it to `/app/key.txt`, one key on a single line and nothing else. You can write it as 16 plain characters or in the dashed XXXX-XXXX-XXXX-XXXX form; the checker drops dashes and spaces and ignores case.

To grade it, we run `java -jar /app/validator.jar "$(cat /app/key.txt)"` and you pass if it prints ACCEPTED. More than one key works, so any accepted key is fine.

# Worth knowing

- You have a full JDK on the box (java, javac, javap).
- Valid keys only use the characters ABCDEFGHJKLMNPQRSTUVWXYZ23456789. There is no I, O, 0, or 1 in the set.
- There are far too many possible keys to try them all, so guessing will not work. You will need to figure out what the checker is actually testing for.
