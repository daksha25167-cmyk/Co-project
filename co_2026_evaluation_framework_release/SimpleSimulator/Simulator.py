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
    regs = [0] * 32
    regs[2] = SP_INIT

    data_mem  = {DATA_START  + i * 4: 0 for i in range(DATA_WORDS)}
    stack_mem = {STACK_START + i * 4: 0 for i in range(32)}


def mem_read(address):
    address = u32(address)
    if DATA_START <= address <= DATA_END:
        return data_mem.get(address, 0)

    elif STACK_START <= address <= STACK_END:
        return stack_mem.get(address, 0)
    return 0


def mem_write(address, value):
    address = u32(address)
    value = u32(value)
    if DATA_START <= address <= DATA_END:
        data_mem[address] = value
    elif STACK_START <= address <= STACK_END:
        stack_mem[address] = value


PC = PC_INIT
trace_lines = []

for _ in range(200000):
    instr = instr_mem.get(PC)
    if instr is None:
        break
    opcode = instr & 0x7F
    next_PC = u32(PC + 4)

        
    if instr == 0b00000000000000000000000001100011:
        current_state = [to_bin32(PC)] + [to_bin32(r) for r in regs]
        trace_lines.append(' '.join(current_state) + ' ')
        mem_lines = []
        for i in range(DATA_WORDS):
            addr = DATA_START + i * 4
            mem_lines.append(
                '0x{:08X}:{}'.format(addr, to_bin32(data_mem.get(addr, 0)))
            )
        return trace_lines, mem_lines


