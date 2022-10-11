import sys, re

registers = {
	"zero": "00000",
	"ra": "00001",
	"sp": "00010",
	"gp": "00011",
	"tp": "00100",
	"t0": "00101",
	"t1": "00110",
	"t2": "00111",
	"s0": "01000",
	"s1": "01001",
	"a0": "01010",
	"a1": "01011",
	"a2": "01100",
	"a3": "01101",
	"a4": "01110",
	"a5": "01111",
	"a6": "10000",
	"a7": "10001",
	"s2": "10010",
	"s3": "10011",
	"s4": "10100",
	"s5": "10101",
	"s6": "10110",
	"s7": "10111",
	"s8": "11000",
	"s9": "11001",
	"s10": "11010",
	"s11": "11011",
	"t3": "11100",
	"t4": "11101",
	"t5": "11110",
	"t6": "11111"
}

def is_binary(num_str):
	return len(num_str) >= 2 and num_str[0:2] == "0b"

def is_hex(num_str):
	return len(num_str) >= 2 and num_str[0:2] == "0x"

def is_int(num_str):
	for chr in num_str:
		if not(chr.isdigit() or chr == '-'):
			return False

	return True

def num_str_to_bin(num_str, base, pad, signed):
	bytes_num = int(num_str, base).to_bytes(4, byteorder="big", signed=signed)
	bin_num = "".join(format(x, '08b') for x in bytes_num)
	
	return bin_num[-pad:]

def val_to_bin(num_str, pad, signed, ref_dict=None):
	if is_binary(num_str):
		return num_str_to_bin(num_str[2:], 2, pad, signed)
	elif is_hex(num_str):
		return num_str_to_bin(num_str[2:], 16, pad, signed)
	elif is_int(num_str):
		return num_str_to_bin(num_str, 10, pad, signed)
	elif ref_dict and num_str in ref_dict:
		return ref_dict[num_str]
	
	raise ValueError(f"{num_str} can not be converted to binary")

def reg_to_bin(num_str):
	if num_str[0] == 'x':
		return num_str_to_bin(num_str[1:], 10, 5, False)
	else:
		return val_to_bin(num_str, 5, False, ref_dict=registers)


def parse_reg_imm(cmd, data):
	groups = re.match(r"([^,]+),(.+)", cmd).groups()
	data.rd = groups[0]
	data.imm = groups[1]

def parse_reg_off_reg(cmd, data):
	groups = re.match(r"([^,]+),([^(]+)\(([^)]+)\)", cmd).groups()
	data.rd = groups[0]
	data.imm = groups[1]
	data.rs1 = groups[2]

def parse_reg_reg_imm(cmd, data):
	groups = re.match(r"([^,]+),([^,]+),(.+)", cmd).groups()
	data.rd = groups[0]
	data.rs1 = groups[1]
	data.imm = groups[2]

def parse_reg_reg_reg(cmd, data):
	groups = re.match(r"([^,]+),([^,]+),(.+)", cmd).groups()
	data.rd = groups[0]
	data.rs1 = groups[1]
	data.rs2 = groups[2]


def ex_rtype(data):
	rd_bin = reg_to_bin(data.rd)
	rs1_bin = reg_to_bin(data.rs1)
	rs2_bin = reg_to_bin(data.rs2)

	return data.funct7 + rs2_bin + rs1_bin + data.funct3 + rd_bin + data.opcode

def ex_itype(data):
	rd_bin = reg_to_bin(data.rd)
	rs1_bin = reg_to_bin(data.rs1)
	imm_bin = val_to_bin(data.imm, 12, True)

	return imm_bin + rs1_bin + data.funct3 + rd_bin + data.opcode

def ex_sitype(data):
	rd_bin = reg_to_bin(data.rd)
	rs1_bin = reg_to_bin(data.rs1)
	imm_bin = val_to_bin(data.imm, 5, False)

	return data.funct7 + imm_bin + rs1_bin + data.funct3 + rd_bin + data.opcode

def ex_stype(data):
	rs1_bin = reg_to_bin(data.rs1)
	rs2_bin = reg_to_bin(data.rd)
	imm_bin = val_to_bin(data.imm, 12, True)

	return imm_bin[-12:-5] + rs2_bin + rs1_bin + data.funct3 + imm_bin[-5:] + data.opcode

def ex_btype(data):
	rd_bin = reg_to_bin(data.rd)
	rs1_bin = reg_to_bin(data.rd)
	rs2_bin = reg_to_bin(data.rs1)
	imm_bin = val_to_bin(data.imm, 13, True)

	return imm_bin[-13] + imm_bin[-11:-5] + rs2_bin + rs1_bin + data.funct3 + imm_bin[-5:-1] + imm_bin[-12] + data.opcode

def ex_utype(data):
	rd_bin = reg_to_bin(data.rd)
	imm_bin = val_to_bin(data.imm, 32, True)

	return imm_bin[-32:-12] + rd_bin + data.opcode

def ex_jtype(data):
	rd_bin = reg_to_bin(data.rd)
	imm_bin = val_to_bin(data.imm, 21, True)

	return imm_bin[-21] + imm_bin[-11:-1] + imm_bin[-12] + imm_bin[-20:-12] + rd_bin + data.opcode


class CommandData:
	def __init__(self, opcode, funct3=None, funct7=None):
		self.opcode = opcode
		self.funct3 = funct3
		self.funct7 = funct7
		self.rd = None
		self.rs1 = None
		self.rs2 = None
		self.imm = None


class CommandHandler:
	def __init__(self, parser, executor, data):
		self.parser = parser
		self.executor = executor
		self.data = data

	def parse(self, command):
		self.parser(command, self.data)

	def execute(self):
		return self.executor(self.data)

handlers = {
	"lui": CommandHandler(parse_reg_imm, ex_utype, CommandData("0110111")),
	"auipc": CommandHandler(parse_reg_imm, ex_utype, CommandData("0010111")),
	"jal": CommandHandler(parse_reg_imm, ex_jtype, CommandData("1101111")),
	"jalr": CommandHandler(parse_reg_off_reg, ex_itype, CommandData("1100111", "000")),
	"beq": CommandHandler(parse_reg_reg_imm, ex_btype, CommandData("1100011", "000")),
	"bne": CommandHandler(parse_reg_reg_imm, ex_btype, CommandData("1100011", "001")),
	"blt": CommandHandler(parse_reg_reg_imm, ex_btype, CommandData("1100011", "100")),
	"bge": CommandHandler(parse_reg_reg_imm, ex_btype, CommandData("1100011", "101")),
	"bltu": CommandHandler(parse_reg_reg_imm, ex_btype, CommandData("1100011", "110")),
	"bgeu": CommandHandler(parse_reg_reg_imm, ex_btype, CommandData("1100011", "111")),
	"lb": CommandHandler(parse_reg_off_reg, ex_itype, CommandData("0000011", "000")),
	"lh": CommandHandler(parse_reg_off_reg, ex_itype, CommandData("0000011", "001")),
	"lw": CommandHandler(parse_reg_off_reg, ex_itype, CommandData("0000011", "010")),
	"lbu": CommandHandler(parse_reg_off_reg, ex_itype, CommandData("0000011", "100")),
	"lhu": CommandHandler(parse_reg_off_reg, ex_itype, CommandData("0000011", "101")),
	"sb": CommandHandler(parse_reg_off_reg, ex_stype, CommandData("0100011", "000")),
	"sh": CommandHandler(parse_reg_off_reg, ex_stype, CommandData("0100011", "001")),
	"sw": CommandHandler(parse_reg_off_reg, ex_stype, CommandData("0100011", "010")),
	"addi": CommandHandler(parse_reg_reg_imm, ex_itype, CommandData("0010011", "000")),
	"slti": CommandHandler(parse_reg_reg_imm, ex_itype, CommandData("0010011", "010")),
	"sltiu": CommandHandler(parse_reg_reg_imm, ex_itype, CommandData("0010011", "011")),
	"xori": CommandHandler(parse_reg_reg_imm, ex_itype, CommandData("0010011", "100")),
	"ori": CommandHandler(parse_reg_reg_imm, ex_itype, CommandData("0010011", "110")),
	"andi": CommandHandler(parse_reg_reg_imm, ex_itype, CommandData("0010011", "111")),
	"slli": CommandHandler(parse_reg_reg_imm, ex_sitype, CommandData("0010011", "000", "0000000")),
	"srli": CommandHandler(parse_reg_reg_imm, ex_sitype, CommandData("0010011", "000", "0000000")),
	"srai": CommandHandler(parse_reg_reg_imm, ex_sitype, CommandData("0010011", "000", "0100000")),
	"add": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0000000")),
	"sub": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0100000")),
	"sll": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0000000")),
	"slt": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0000000")),
	"sltu": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0000000")),
	"xor": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0000000")),
	"srl": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0000000")),
	"sra": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0100000")),
	"or": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0000000")),
	"and": CommandHandler(parse_reg_reg_reg, ex_rtype, CommandData("0110011", "000", "0000000"))
}


if __name__ == "__main__":
	cmd_str = sys.argv[1].strip().lower()
	parts = cmd_str.split(" ")
	title = parts[0]
	tail = "".join(parts[1:])

	handler = handlers[title]
	handler.parse(tail)
	output = handler.execute()

	print(output)

