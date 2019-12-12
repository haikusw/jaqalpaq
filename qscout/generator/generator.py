from qscout.core import GateStatement, GateBlock, LoopStatement, Register, NamedQubit, Constant, Parameter

def notate_slice(s):
	if s.step:
		return "%s:%s:%s" % (s.start or 0, s.stop, s.step)
	else:
		return "%s:%s" % (s.start or 0, s.stop)

def generate_jaqal_program(circ):
	program = ""
	for register in circ.registers.values():
		if register.fundamental:
			program += generate_jaqal_reg(register)
	program += "\n"
	for const in circ.constants.values():
		program += generate_jaqal_let(const)
	if circ.constants: program += "\n"
	for register in circ.registers.values():
		if not register.fundamental:
			program += generate_jaqal_map(register)
	if len(circ.registers) > 1: program += "\n"
	for macro in circ.macros.values():
		program += generate_jaqal_macro(macro)
	for statement in circ.gates.gates:
		if isinstance(statement, GateStatement):
			program += generate_jaqal_gate(statement, 0)
		elif isinstance(statement, LoopStatement):
			program += generate_jaqal_loop(statement, 0)
		elif isinstance(statement, GateBlock):
			program += generate_jaqal_block(statement, 0, True)
	return program

def generate_jaqal_reg(register): # TODO: Support let-expression parametrized indices
	return "reg " + register.name + "[" + str(register.size) + "]\n"

def generate_jaqal_let(const):
	return "let " + const.name + " " + generate_jaqal_value(const.value) + "\n"

def generate_jaqal_map(register): # TODO: Support let-expression parametrized indices
	if isinstance(register, NamedQubit):
		return "map " + register.name + " " + register.alias_from.name + "[" + str(register.alias_index) + "]\n"
	else:
		return "map " + register.name + "[" + str(register.size) + "] " + register.alias_from.name + "[" + notate_slice(register.alias_slice) + "]\n"

def generate_jaqal_macro(macro):
	return "macro " + macro.name + " " + " ".join([parameter.name for parameter in macro.parameters]) + " " + generate_jaqal_block(macro.body, 0, False) + "\n"

def generate_jaqal_gate(statement, depth):
	return "\t" * depth + statement.name + " " + " ".join([generate_jaqal_value(val) for val in statement.parameters.values()]) + "\n"

def generate_jaqal_loop(statement, depth):
	return "\t" * depth + "loop " + generate_jaqal_value(statement.iterations) + " " + generate_jaqal_block(statement.gates, depth, False)

def generate_jaqal_block(statement, depth, indent_first_line):
	output = ""
	if indent_first_line:
		output += "\t" * depth
	if statement.parallel:
		output += "<\n"
	else:
		output += "{\n"
	for gate in statement.gates:
		if isinstance(gate, GateStatement):
			output += generate_jaqal_gate(gate, depth+1)
		elif isinstance(gate, LoopStatement):
			output += generate_jaqal_loop(gate, depth+1)
		elif isinstance(gate, GateBlock):
			output += generate_jaqal_block(gate, depth+1, True)
	output += "\t" * depth
	if statement.parallel:
		output += ">\n"
	else:
		output += "}\n"
	return output

def generate_jaqal_value(val):
	if isinstance(val, Constant) or isinstance(val, NamedQubit) or isinstance(val, Parameter):
		return val.name
	elif isinstance(val, float) or isinstance(val, int):
		return str(val) # TODO: Request that we support scientific notation on angle parameters, or else fix this to not use scientific notation!