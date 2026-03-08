import sys

#register names
reg={"zero":"00000", "x0":"00000", "ra":"00001", "x1":"00001", "sp":"00010", "x2":"00010", "gp":"00011", "x3":"00011", "tp":"00100", "x4":"00100", "t0":"00101", "x5":"00101", "t1":"00110", "x6":"00110", "t2":"00111", "x7":"00111", "s0":"01000", "fp":"01000", "x8":"01000", "s1":"01001", "x9":"01001", "a0":"01010", "x10":"01010", "a1":"01011", "x11":"01011", "a2":"01100", "x12":"01100", "a3":"01101", "x13":"01101", "a4":"01110", "x14":"01110", "a5":"01111", "x15":"01111", "a6":"10000", "x16":"10000", "a7":"10001", "x17":"10001", "s2":"10010", "x18":"10010", "s3":"10011", "x19":"10011", "s4":"10100", "x20":"10100", "s5":"10101", "x21":"10101", "s6":"10110", "x22":"10110", "s7":"10111", "x23":"10111", "s8":"11000", "x24":"11000", "s9":"11001", "x25":"11001", "s10":"11010", "x26":"11010", "s11":"11011", "x27":"11011", "t3":"11100", "x28":"11100", "t4":"11101", "x29":"11101", "t5":"11110", "x30":"11110", "t6":"11111", "x31":"11111",}
#func3 is of size 3 and func 7 is of size 7 {op:(func7,func3)}
r_type={"add":("0000000", "000"), "sub":("0100000","000"), "sll":("0000000","001"), "srl":("0000000","101"), "slt":("0000000","010"), "sltu":("0000000","011"), "or":("0000000","110"), "and":("0000000","111"), "xor":("0000000","100"), "opcode":"0110011"}
#{op:(func3,opcode)}
i_type={"addi":("000","0010011"), "sltiu":("011","0010011"), "lw":("010","0000011"), "jalr":("000","1100111")}
#{op:func3}
s_type={"sw":"010", "opcode":"0100011"}
#{op:func3}
b_type={"beq":"000", "bne":"001", "blt":"100", "bge":"101", "bltu":"110", "bgeu":"111", "opcode":"1100011"}
#{op:opcode}
u_type={"lui":"0110111", "auipc":"0010111"}
#{op:opcode}
j_type={"jal":"1101111"}



def error(line_no,msg):
    print(f"Error found at line {line_no}:{msg}")
    sys.exit(1)

def check_reg(name, line_no):
    if name not in reg:
        error(line_no,f"Unknown register '{name}'")

def check_imm(val_str,bits,line_no):
    try:
        val=int(val_str)
    except ValueError:
        error(line_no,f"Invalid immediate value: '{val_str}'")
    lo=-(1<<(bits-1))
    hi=(1<<(bits-1))-1
    if val<lo or val>hi:
        error(line_no,f"Immediate '{val_str}' out of {bits}-bit signed range [{lo}, {hi}]")
    return val


def immediate_to_binary(val, bits):
    val = int(val)
    lower = -(2**(bits-1))
    upper= (2**(bits-1))-1
    if val <lower or val>upper:
        print("Immediate Value Out of Range")
        sys.exit(1)
    if val < 0:
        val = (1 << bits) + val
    binary = bin(val)[2:]
    while len(binary) < bits:
        binary = "0" + binary
    return binary



def encode_rtype(instructions, rd, rs1, rs2,line_no):
    check_reg(rd,line_no)
    check_reg(rs1,line_no)
    check_reg(rs2,line_no)
    funct7,funct3= r_type[instructions]
    opcode = "0110011"
    rd_binary = reg[rd]
    rs1_binary = reg[rs1]
    rs2_binary = reg[rs2]
    binary = (funct7 + rs2_binary + rs1_binary + funct3 + rd_binary + opcode)
    return binary


def encode_itype(instructions, rd, rs1, immediate,line_no):
    check_reg(rd,line_no)
    check_reg(rs1,line_no)
    check_imm(immediate,12,line_no)
    funct3,opcode= i_type[instructions]
    rd_binary = reg[rd]
    rs1_binary = reg[rs1]
    imm_bin = immediate_to_binary(immediate,12)
    binary = imm_bin + rs1_binary + funct3 + rd_binary + opcode
    return binary


def encode_lw(rd, operand,line_no):
    if "(" not in operand or not operand.endswith(")"):
        error(line_no,"lw expects format: rd, offset(rs1)")
    offset,reg_part= operand.split("(")
    rs1 = reg_part[:-1]
    return encode_itype("lw", rd, rs1, offset,line_no)

def encode_sw(rs2,operand,line_no):
    if "(" not in operand or not operand.endswith(")"):
        error(line_no,"sw expects format: rs2, offset(rs1)")
    offset,rest=operand.split("(")
    rs1=rest.strip(")")
    check_reg(rs2,line_no)
    check_reg(rs1,line_no)
    check_imm(offset,12,line_no)
    func3,opcode=s_type["sw"],s_type['opcode']
    imm=immediate_to_binary(offset,12)
    imm1=imm[0:7]
    imm2=imm[7:12]
    return imm1+reg[rs2]+reg[rs1]+func3+imm2+opcode
def encode_btype(inst,rs1,rs2,offset,line_no):
    check_reg(rs1,line_no)
    check_reg(rs2,line_no)
    if offset<-4096 or offset>4094:
        error(line_no,f"Branch offset {offset} out of 13-bit range")
    func3=b_type[inst]
    opcode=b_type['opcode']
    imm=immediate_to_binary(offset,13)
    imm1=imm[0]
    imm2=imm[1]
    imm3=imm[2:8]
    imm4=imm[8:12]
    return imm1+imm3+reg[rs2]+reg[rs1]+func3+imm4+imm2+opcode
def encode_utype(inst,rd,immediate,line_no):
    check_reg(rd,line_no)
    check_imm(immediate,20,line_no)
    opcode=u_type[inst]
    imm=immediate_to_binary(immediate,20)
    return imm+reg[rd]+opcode
def encode_jtype(rd,offset,line_no):
    check_reg(rd,line_no)
    if offset<-1048576 or offset>1048574:
        error(line_no,f"JAL offset {offset} out of 21-bit range")
    opcode=j_type['jal']
    imm=immediate_to_binary(offset,21)
    imm1=imm[0]
    imm2=imm[1:9]
    imm3=imm[9]
    imm4=imm[10:20]
    return imm1+imm4+imm3+imm2+reg[rd]+opcode
def encode_jalr(rd,rs1,immediate,line_no):
    return encode_itype('jalr',rd,rs1,immediate,line_no)



def pass1(input_file):
    try:
        with open(input_file) as f:
            lines = f.readlines()

    except FileNotFoundError:
        print("Error cannot open input file")
        sys.exit(1)

    pc =0
    labels={}
    cleaned_lines=[]

    line_no = 0
    for line in lines:
        line_no +=1

        text=line.strip()

        if text=="":
            continue

        if ":" in text:
            parts=text.split(":")

            if len(parts)>2 :
                error(line_no,"Multiple colons found.Invalid label format.")
            
            
            label=parts[0].strip()

            if parts[0]!=label:
                error(line_no,"Inavlid spacing.No space found between label and colon")

            if not label or not label[0].isalpha():
                error(line_no,"Invalid label name.Must start with charecter")

            if label in labels:
                error(line_no,f"Duplicate label found: {label}")


        
            labels[label]= pc

            instructions=parts[1].strip()

            if instructions!="":
                cleaned_lines.append((line_no,pc,instructions))
                pc=pc+4

        else:
            cleaned_lines.append((line_no,pc,text))
            pc=pc+4

    return cleaned_lines,labels


def encode_instruction(line_no,pc,instruction,labels):
    t=instruction.replace(',',' ').split()
    op=t[0].lower()
    if op in r_type and op!='opcode':
        if len(t)!=4:
            error(line_no,f"R-type '{op}' expects: rd,rs1,rs2")
        return encode_rtype(op,t[1],t[2],t[3],line_no)
    
    if  op in ("addi","sltiu"):
        if len(t)!=4:
            error(line_no,f"I-type '{op}' expects: rd,rs1,imm")
        return encode_itype(op,t[1],t[2],t[3],line_no)
    
    if op=='lw':
        if len(t)!=3:
            error(line_no,f"lw expects: rd, offset(rs1)")
        return encode_lw(t[1],t[2],line_no)
    
    if op=='jalr':
        if len(t)==3 and '(' in t[2]:
            offset,rest=t[2].split('(')
            rs1=rest.rstrip(")")
            return encode_jalr(t[1],rs1,offset,line_no)
        elif len(t)==4:
            return encode_jalr(t[1],t[2],t[3],line_no)
        else:
            error(line_no,"jalr expects: rd,rs1,imm or rd,offset(rs1)")
    
    if op in s_type and op!="opcode":
        if len(t)!=3:
            error(line_no,"s_type '{op}' expects: rs2,offset(rs1)")
        return encode_sw(t[1],t[2],line_no)
    
    if op in b_type and op!='opcode':
        if len(t)!=4:
            error(line_no,f"b_type '{op}' expects: rs1,rs2,label/offset")
        target=t[3]
        if target in labels :
            offset=(labels[target]-pc)
        else:
            try: offset=int(target)
            except ValueError: error(line_no,f"Undefined label or invalid offset: '{target}'")
        return encode_btype(op,t[1],t[2],offset,line_no)

    if op in u_type:
        if len(t)!=3:
            error(line_no,f"u_type '{op}' expects: rd,imm")
        return encode_utype(op,t[1],t[2],line_no)
    
    if op=='jal':
        if len(t)!=3:
            error(line_no,f"j_type '{op}' expects: rd,offset/label")
        target=t[2]
        if target in labels :
            offset=(labels[target]-pc)
        else:
            try: offset=int(target)
            except ValueError: error(line_no,f"Undefined label or invalid offset: '{target}'")
        return encode_jtype(t[1],offset,line_no)

    error(line_no,f"Unknown instruction: '{op}'")

def resolve_label_or_int_safe(target, labels, pc):
    if target in labels:
        return labels[target] - pc
    try: 
        return int(target)
    except: 
        return None

def check_virtual_halt(cleaned_lines, labels):
    for _, pc, instr in cleaned_lines:
        t=instr.replace(","," ").split()
        if len(t)==4 and t[0].lower()=="beq":
            if t[1] in ("zero", "x0") and t[2] in ("zero", "x0"):
                offset=resolve_label_or_int_safe(t[3], labels, pc)
                if offset==0:
                    return True
    return False



def main():
    if len(sys.argv)<3:
        print("Usage:python pass1.py input.asm")
        sys.exit(1)
    input_file= sys.argv[1]
    output_file=sys.argv[2]
    cleaned_lines,labels=pass1(input_file)
    output_lines=[]
    if not check_virtual_halt(cleaned_lines, labels):
        error(len(cleaned_lines), "Missing Virtual Halt instruction (beq zero,zero,0)")
    for line_no,pc,instructions in cleaned_lines:
        binary=encode_instruction(line_no,pc,instructions,labels)
        output_lines.append(binary)
    with open(output_file,'w') as f:
        f.write('\n'.join(output_lines))


main()



