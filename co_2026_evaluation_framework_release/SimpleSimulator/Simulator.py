import sys

PC_INIT     = 0x00000000
SP_INIT     = 0x0000017C
DATA_START  = 0x00010000
DATA_END    = 0x0001007F
STACK_START = 0x00000100
STACK_END   = 0x0000017F
DATA_WORDS  = 32

def to_bin32(val):
    return '0b' + format(val & 0xFFFFFFFF, '032b')

def sign_ext(val, bits):
    if val & (1 << (bits - 1)):
        val -= (1 << bits)
    return val

def to_int32(val):
    val = val & 0xFFFFFFFF
    return val - 0x100000000 if val >= 0x80000000 else val

def u32(val):
    return val & 0xFFFFFFFF

def is_valid_mem(addr):
    # Must be word-aligned (multiple of 4) and in a valid region
    if addr % 4 != 0:
        return False
    if DATA_START <= addr <= DATA_END:
        return True
    if STACK_START <= addr <= STACK_END:
        return True
    return False

def simulate(bin_lines):
    instr_mem = {}
    addr = PC_INIT
    for line in bin_lines:
        line = line.strip()
        if line:
            instr_mem[addr] = int(line, 2)
            addr += 4
