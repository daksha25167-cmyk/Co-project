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
    
        if opcode== 0b0110011:
            rd=(instr>>7)&0x1F; f3=(instr>>12)&0x7; rs1=(instr>>15)&0x1F; rs2=(instr>>20)&0x1F; f7=(instr>>25)&0x7F
            v1,v2=to_int32(regs[rs1]),to_int32(regs[rs2]); u1,u2=regs[rs1],regs[rs2]
            if f3==0: r=u32(v1+v2) if f7==0 else u32(v1-v2)
            elif f3== 1: r=u32(u1<< (u2&0x1F))
            elif f3==2: r=1 if v1<v2 else 0
            elif f3== 3: r=1 if u1<u2 else 0
            elif f3 ==4: r=u1^u2
            elif f3==5: r= u1>>(u2&0x1F)
            elif f3 ==6: r= u1|u2
            else: r=u1&u2
            if rd: regs[rd] =u32(r)

        elif opcode== 0b0010011:
            rd=(instr>>7)&0x1F; f3=(instr>>12)&0x7; rs1=(instr>>15)&0x1F
            imm=sign_ext((instr>> 20)&0xFFF,12)
            if f3==0: r=u32(to_int32(regs[rs1])+ imm)
            elif f3==3: r=1 if regs[rs1] <u32(imm) else 0
            else: r=0
            if rd: regs[rd] =r

        elif opcode== 0b0000011:   
            rd= (instr>>7)&0x1F; f3= (instr>>12)&0x7; rs1=(instr >>15)&0x1F
            imm=sign_ext((instr >>20)&0xFFF,12)
            if f3 ==2:
                ea= u32(to_int32(regs[rs1])+imm)
                # Invalid memory access: stop immediately, no more output
                if not is_valid_mem(ea):
                    return trace_lines, []
                if rd: regs[rd]= u32(mem_read(ea))

        elif opcode==0b1100111:   
            rd= (instr >>7)&0x1F; rs1=(instr >>15)&0x1F
            imm=sign_ext((instr>>20)&0xFFF,12)
            ret=u32(PC+ 4); next_PC= u32((to_int32(regs[rs1])+imm)&~1)
            if rd: regs[rd] =ret

        elif opcode== 0b0100011:   
            f3= (instr>>12)&0x7; rs1=(instr>>15)&0x1F; rs2=(instr>>20)&0x1F
            imm= sign_ext((((instr>>25)&0x7F)<<5)|((instr>>7)&0x1F),12)
            if f3 ==2:
                ea =u32(to_int32(regs[rs1])+imm)
                # invalid memry access:stop immediately,no more output
                if not is_valid_mem(ea):
                    return trace_lines, []
                mem_write(ea,regs[rs2])

        elif opcode == 0b1100011:   
            f3=(instr>>12)&0x7
            rs1=(instr>>15)&0x1F
            rs2=(instr>>20)&0x1F
            imm=sign_ext(((instr>>31)&1)<<12|
                        ((instr>>7)&1)<<11|
                        ((instr>>25)&0x3F)<<5|
                        ((instr>>8)&0xF)<<1,13)
            v1,v2=to_int32(regs[rs1]),to_int32(regs[rs2])
            u1,u2=regs[rs1],regs[rs2]
            br=((f3==0 and v1==v2)or
                (f3==1 and v1!=v2)or
                (f3==4 and v1<v2)or
                (f3==5 and v1>=v2)or
                (f3==6 and u1<u2)or
                (f3==7 and u1>=u2))
            
            next_PC=u32(PC+imm) if br else u32(PC+4)

        elif opcode==0b0110111:  
            rd=(instr>>7)&0x1F
            if rd:regs[rd]=instr&0xFFFFF000

        elif opcode == 0b0010111:   
            rd=(instr>>7)&0x1F
            if rd!=0:
                regs[rd]=u32(PC+(instr&0xFFFFF000))

        elif opcode == 0b1101111:  
            rd=(instr>>7)&0x1F
            imm=sign_ext(((instr>>31)&0x1)<<20 |
                        ((instr>>12)&0xFF)<<12|
                        ((instr>>20)&0x1)<<11|
                        ((instr>>21)&0x3FF)<<1,21)
            if rd!=0:
                regs[rd]=u32(PC+4)
            next_PC=u32(PC+imm)

        regs[0]=0
        PC=next_PC
        trace_parts=[to_bin32(PC)]+[to_bin32(r) for r in regs]

        trace_lines.append(f"{' '.join(trace_parts)}")

    mem_lines=[f"0x{DATA_START+i*4:08x}:{to_bin32(data_mem.get(DATA_START+i*4,0))}" for i in range(DATA_WORDS)]
    return trace_lines,mem_lines

def main():
    if len(sys.argv)<3:
        print("Usage: python3 Simulator.py <bin_file> <trace_file>")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        lines=f.readlines()
    trace,mem=simulate(lines)
    output=trace+mem
    with open(sys.argv[2],'w') as f:
        f.write('\n'.join(output)+'\n')
    if len(sys.argv)>3:
        with open(sys.argv[3],'w') as f:
            f.write('\n'.join(output)+'\n')

if __name__=='__main__':
    main()
