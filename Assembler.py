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

        line=line.strip()

        if line=="":
            continue

        if ":" in line:
            parts=line.split(":")

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
                cleaned_lines.append((line_no,instructions))
                pc=pc+4

        else:
            cleaned_lines.append((line_no,line))
            pc=pc+4

    return cleaned_lines,labels


def is_virtual_halt(op, operands):
    if op!="beq":
        return False
    if len(operands)!=3:
        return False
    rs1 =operands[0].strip().lower()
    rs2= operands[1].strip().lower()
    imm= operands[2].strip()      

    zero_names= ("zero", "x0")
    return rs1 in zero_names and rs2 in zero_names and imm== "0"


def check_errors(cleaned_lines):
    """
    error 1: wrong instructions
    error 2: immediate is out of bounds
    error 3: Missing virtual halt
    error 4: virtual halt is not the last instruction
    """
    val_inst= [
        "add","sub","sll", "srl","slt","sltu","or", "and","xor","addi", "sltiu", "lw", "jalr","sw","beq", "bne", "blt", "bge", "bltu", "bgeu", "lui", "auipc","jal"
    ]

    if not cleaned_lines:
        print("Error: No instructions found in the file.")
        sys.exit(1)


    instr_list= []
    for line_no, instr in cleaned_lines:
        parts=instr.split(None, 1)        
        op= parts[0].strip().lower()
        if len(parts)> 1:
            operands=[o.strip() for o in parts[1].split(",")]
        else:
            operands =[]
        instr_list.append((line_no, op, operands))

    # error 1
    for line_no,op,operands in instr_list:
        if op not in val_inst:
            error(line_no, f"Unknown instruction '{op}'. ")

        for operand in operands:
            operand=operand.strip().lower()
            if operand.lstrip("-").isdigit():
                continue
            if "(" in operand:
                continue
            if operand not in reg:
                error(line_no, f"Unknown register '{operand}'.")

    # error 2 is taken by immediate_to_binary function 
    #error 3
    last_line_no, last_op, last_operands= instr_list[-1]
    if not is_virtual_halt(last_op,last_operands):
        error(last_line_no, "Last instruction must be Virtual Halt: beq zero,zero,0")

    #error 4
    for line_no, op, operands in instr_list[:-1]:
        if is_virtual_halt(op, operands):
            error(line_no, "Virtual Halt (beq zero,zero,0) must only be the last instruction.")

def immediate_to_binary(val, bits):

    val = int(val)

    if val < 0:
        val = (1 << bits) + val

    binary = bin(val)[2:]

    while len(binary) < bits:
        binary = "0" + binary

    return binary



def encode_rtype(instructions, rd, rs1, rs2):

    funct7,funct3= r_type[instructions]
    
    
    opcode = "0110011"

    rd_binary = reg[rd]
    rs1_binary = reg[rs1]
    rs2_binary = reg[rs2]

    binary = (funct7 + rs2_binary + rs1_binary + funct3 + rd_binary + opcode)

    return binary


def encode_itype(instructions, rd, rs1, immediate):

    funct3,opcode= i_type[instructions]
   

    rd_binary = reg[rd]
    rs1_binary = reg[rs1]

    imm_bin = immediate_to_binary(immediate,12)

    binary = imm_bin + rs1_binary + funct3 + rd_binary + opcode

    return binary


def encode_lw(rd, operand):

    offset,reg_part= operand.split("(")
   
    rs1 = reg_part[:-1]

    return encode_itype("lw", rd, rs1, offset)


def main():
    
    if len(sys.argv)!=2:
        print("Usage:python pass1.py input.asm")
        sys.exit(1)

    input_file= sys.argv[1]
    

    cleaned_lines,labels=pass1(input_file)
    check_errors(cleaned_lines) 

    print("Label Table")

    for label in labels:
        print(f"{label}->{labels[label]}")

    print("Cleaned instructions")

    for line_no,instructions in cleaned_lines:

        print(f"{line_no}:{instructions}")

main()