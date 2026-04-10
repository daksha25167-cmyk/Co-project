import sys
regs = [0] * 32
regs[2] = 380
DATA_START  = 0x00010000
STACK_START = 0x00000100
STACK_END   = 0x0000017F
data_mem  = {DATA_START  + i * 4: 0 for i in range(32)}
stack_mem = {STACK_START + i * 4: 0 for i in range(32)}

def load_program(bin_file):
    instr_mem = {}
    try:
        with open(bin_file, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: cannot open {bin_file}")
        sys.exit(1)
    addr = 0
    for line in lines:
        line = line.strip()
        if line:
            instr_mem[addr] = int(line, 2)
            addr += 4
    return instr_mem

def to_bin32(val):
    return '0b' + format(val & 0xFFFFFFFF, '032b')

def to_int32(val):
    val = val & 0xFFFFFFFF
    if val >= 0x80000000:
        val -= 0x100000000
    return val

def u32(val):
    return val & 0xFFFFFFFF

def sign_ext(val, bits):
    if val & (1 << (bits - 1)):
        val -= (1 << bits)
    return val

def mem_read(address):
    address = u32(address)
    if DATA_START <= address <= DATA_START + 0x7C:
        return data_mem.get(address, 0)
    if STACK_START <= address <= STACK_END:
        return stack_mem.get(address, 0)
    return 0

def mem_write(address, value):
    address = u32(address)
    value   = u32(value)
    if DATA_START <= address <= DATA_START + 0x7C:
        data_mem[address] = value
    elif STACK_START <= address <= STACK_END:
        stack_mem[address] = value

def print_state(PC):
    parts = [to_bin32(PC)] + [to_bin32(r) for r in regs]
    print(' '.join(parts) + ' ')

def print_memory():
    for i in range(32):
        addr = DATA_START + i * 4
        print(f'0x{addr:08X}:{to_bin32(data_mem.get(addr, 0))}')


def decode_rtype(instr):
    rd     = (instr >>  7) & 0x1F   # bits [11:7]
    funct3 = (instr >> 12) & 0x07
    rs1    = (instr >> 15) & 0x1F
    rs2    = (instr >> 20) & 0x1F
    funct7 = (instr >> 25) & 0x7F
    v1 = to_int32(regs[rs1])
    v2 = to_int32(regs[rs2])
    u1 = regs[rs1]
    u2 = regs[rs2]
    if funct3 == 0b000:
        if funct7 == 0b0000000:
            result = u32(v1 + v2)
        elif funct7 == 0b0100000:
            result = u32(v1 - v2)
        else:
            result = 0
    elif funct3 == 0b001:
        shamt  = u2 & 0x1F
        result = u32(u1 << shamt)
    elif funct3 == 0b010:
        result = 1 if v1 < v2 else 0
    elif funct3 == 0b011:
        result = 1 if u1 < u2 else 0
    elif funct3 == 0b100:
        result = u1 ^ u2
    elif funct3 == 0b101:
        shamt  = u2 & 0x1F
        result = u1 >> shamt
    elif funct3 == 0b110:
        result = u1 | u2
    elif funct3 == 0b111:
        result = u1 & u2
    else:
        result = 0
    if rd != 0:
        regs[rd] = result

def run(bin_file, trace_file, read_trace_file=None):
    global regs, data_mem, stack_mem
    instr_mem = load_program(bin_file)
    PC = 0
    output_lines = []
    while True:
        instr = instr_mem.get(PC)
        if instr is None:
            break
        opcode = instr & 0x7F
        if instr == 0b00000000000000000000000001100011:
            regs[0] = 0
            parts = [to_bin32(PC)] + [to_bin32(r) for r in regs]
            output_lines.append(' '.join(parts) + ' ')
            break
        next_PC = u32(PC + 4)

        elif opcode == 0b0010011:   
            rd = (instr >> 7) & 0x1F
            funct3 = (instr >> 12) & 0x07
            rs1 = (instr >> 15) & 0x1F

            imm = sign_ext((instr >> 20) & 0xFFF, 12)

            if funct3 == 0b000:   # addi
                result = u32(to_int32(regs[rs1]) + imm)

            elif funct3 == 0b011: # sltiu
                result = 1 if regs[rs1] < u32(imm) else 0

            else:
                result = 0

            if rd != 0:
                regs[rd] = result
        # ── Person 3 will add B-type, J-type here ─────────────────────────────
        # ── Person 4 will add U-type, memory dump, file output here ───────────
        regs[0] = 0
        PC = next_PC
        parts = [to_bin32(PC)] + [to_bin32(r) for r in regs]
        output_lines.append(' '.join(parts) + ' ')
    for i in range(32):
        addr = DATA_START + i * 4
        output_lines.append(f'0x{addr:08X}:{to_bin32(data_mem.get(addr, 0))}')
    with open(trace_file, 'w') as f:
        f.write('\n'.join(output_lines) + '\n')
    if read_trace_file:
        with open(read_trace_file, 'w') as f:
            f.write('\n'.join(output_lines) + '\n')


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 Simulator.py <bin_file> <trace_file> [read_trace_file]")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
