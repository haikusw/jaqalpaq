from qscout.core import GateStatement, GateBlock, LoopStatement, Register, NamedQubit

def notate_slice(s):
	if s.step:
		return "%s:%s:%s" % (s.start or 0, s.stop, s.step)
	else:
		return "%s:%s" % (s.start or 0, s.stop)

def generate_qasm_program(circ):
	program = ""
	for register in circ.registers:
		if register.fundamental:
			program += generate_qasm_reg(register)
	program += "\n"
	for const in circ.constants:
		program += generate_qasm_let(const)
	program += "\n"
	for register in circ.registers:
		if not register.fundamental:
			program += generate_qasm_map(register)
	program += "\n"
	for macro in circ.macros:
		program += generate_qasm_macro(macro)
	for statement in circ.gates:
		if isinstance(statement, GateStatement):
			program += generate_qasm_gate(statement, 0)
		elif isinstance(statement, LoopStatement):
			program += generate_qasm_loop(statement, 0)
		elif isinstance(statement, GateBlock):
			program += generate_qasm_block(statement, 0, True)
	return program

def generate_qasm_reg(register):
	return "reg " + register.name + "[" + register.size + "]\n"

def generate_qasm_let(const):
	return "let " + const.name + " " + const.value + "\n"

def generate_qasm_map(register):
	if isinstance(register, NamedQubit):
		return "map " + register.name + " " + register.alias_from.name + "[" + str(register.alias_index) + "]\n"
	else:
		return "map " + register.name + " [" + register.size + "]" + register.alias_from.name + "[" + notate_slice(register.alias_slice) + "]\n"

def generate_qasm_macro(macro):
	return "macro " + macro.name + " " + " ".join([parameter.name for parameter in macro.parameters]) + " " + generate_qasm_block(macro.body, 0, False) + "\n"

def generate_qasm_gate(statement, depth):
	return "\t" * depth + statement.name + " ".join([str(val) for key, val in statement.parameters]) + "\n"

def generate_qasm_loop(statement, depth):
	return "\t" * depth + "loop " + str(statement.iterations) + generate_qasm_block(statement.gates, depth, False)

def generate_qasm_block(statement, depth, indent_first_line):
	output = ""
	if indent_first_line:
		output += "\t" * depth
	if statement.parallel:
		output += "<\n"
	else:
		output += "{\n"
	for gate in statement.gates:
		output += generate_qasm_gate(gate, depth+1)
	output += "\t" * depth
	if statement.parallel:
		output += ">\n"
	else:
		output += "}\n"
	return output
