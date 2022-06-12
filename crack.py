from z3 import *

import sys

old_stdout = sys.stdout
isatty = old_stdout.isatty()
encoding = old_stdout.encoding

if not isatty:
    sys.stdout = sys.stderr

from sys import stderr

progress_bar = False
alive_bar2 = None
try:
    from alive_progress import alive_bar
    alive_bar2 = alive_bar
    progress_bar = True
except:
    pass

def eprint(*args, **kwargs):
    print(*args, file=stderr, **kwargs)

def u32(x):
    return x & 0xffff_ffff

def reflect8(x):
    return int(f"{x:08b}"[::-1], 2)

def reflect32(x):
    return int(f"{x:032b}"[::-1], 2)

UPPER_BIT = 1 << 31

def upper_bit(x):
    return (x & UPPER_BIT) != 0

def crc32(string):
    if type(string) is str:
        string = string.encode()
    POLY = 0x04c11db7
    crc = u32(-1)
    for byte in string:
        crc = crc ^ (reflect8(byte) << 24)
        for _ in range(8):
            crc = ((crc << 1) ^ POLY) if upper_bit(crc) else (crc << 1)

    return reflect32(u32(~crc))

# ============= Parameters ==============

# Plaintext for sanity checking
plaintext = None

# Length of string to solve for
length = 0x10

# Hash to solve for
crc_to_crack = 0xb5b69a26

# Beginning of string must match
prefix = "ex_bad_"

# End of string must match
suffix = ""

# Substring must be present at least once
substring = ""

# =======================================

def reflect8_smt(val):
    return Concat(*([Extract(i, i, val) for i in range(8)]))

def reflect32_smt(val):
    return Concat(*([Extract(i, i, val) for i in range(32)]))

def crc32_smt(input_str):
    crc = BitVecVal(u32(-1), 32)
    POLY = BitVecVal(0x04c11db7, 32)

    for byte in input_str:
        crc = crc ^ Concat(reflect8_smt(byte), BitVecVal(0, 24))

        for _ in range(8):
            upper_bit = Extract(31, 31, crc)
            crc = If(upper_bit == 1, (crc << 1) ^ POLY, (crc << 1))

    return reflect32_smt(crc ^ u32(-1))

input_str = [BitVec("s" + str(i), 8) for i in range(length)]

solver = Solver()

solver.add(crc32_smt(input_str) == crc_to_crack)

# No double underscores
for i in range(len(input_str) - 1):
    solver.add(Not(And(input_str[i] == ord('_'), input_str[i + 1] == ord('_'))))

# All characters are a-z, 0-9, or _
for char in input_str[len(prefix):]:
    solver.add(Or(And(char >= ord('0'), char <= ord('9')), And(char >= ord('a'), char <= ord('z')), char == ord('_')))

# Prefix must match
for i, char in enumerate(prefix):
    solver.add(input_str[i] == ord(char))

# Substring match must be found
if len(substring) != 0:
    possible_windows = []
    for i in range(0, len(input_str) - len(substring)):
        possible_windows.append(And(*[
            input_str[i+j] == ord(char) for j, char in enumerate(substring)
        ]))

    solver.add(Or(*possible_windows))

# Suffix must match
for i, char in enumerate(suffix[::-1]):
    solver.add(input_str[-(i+1)] == ord(char))

if progress_bar:
    alive_bar = lambda: alive_bar2(
        #unknown="dots_waves",
        #calibrate=40,
        title=f"Cracking {hex(crc_to_crack)}",
        enrich_print=False
    )
else:
    eprint("cracking:", hex(crc_to_crack))

    class Test:
        def __enter__(self, *args, **kwargs):
            return self

        def __exit__(self, *args, **kwargs):
            pass

        def __call__(self, *args, **kwargs):
            pass

    alive_bar = lambda: Test()

with alive_bar() as bar:
    if progress_bar:
        sys.stdout.encoding = encoding

    while solver.check() == sat:
        model = solver.model()
        solution_bytes = bytes([model[byte].as_long() for byte in input_str])

        val = None
        try:
            val = bytes([model[byte].as_long() for byte in input_str]).decode()
        except:
            pass

        if plaintext is None:
            if isatty:
                print(f"{val}")
            else:
                print(f"{val}", file=old_stdout)
        elif val == plaintext:
            eprint("Success!")
            exit()

        solver.add(Not(And(*[byte == model[byte].as_long() for byte in input_str])))
        bar()

eprint("Done")
