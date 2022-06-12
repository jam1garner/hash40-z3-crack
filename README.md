# hash40-z3-crack

A hash cracker that utilized z3 in order to leverage SMT solving for optimizing hash cracking of
hash40 hashes from Smash Ultimate using complex rules/constraints in order to produce higher quality
matches for a given hash.

Output will be newline separated when piped to a file. Progress bar and other human-focused output
will not be included when stdout is piped to a file or another process.

### Required Dependencies

* z3

```
pip install z3-solver
```

### Optional Dependencies (Progress Bar)

To have a progress bar run the following:

```
pip install alive-progress
```
