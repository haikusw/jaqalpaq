import ply.yacc as yacc
from qscout.core import GateBlock, LoopStatement, ScheduledCircuit, Constant, GateStatement, GateDefinition, Macro, Parameter, Register, NamedQubit
from qscout import QSCOUTError
from qscout.parser.lexer import get_lexer, tokens # IMPORTANT: PLY has a bad time if this is a relative import, for some reason.

def p_program(p):
	'program : header_statements body_statements'
	c = ScheduledCircuit(True)
	def resolve_id(name, params, allow_reg=True):
		if name is None:
			return None
		elif name in c.registers and allow_reg:
			return (c.registers[name])
		elif name in c.constants:
			return (c.constants[name])
		elif name in params:
			return (params[name])
		elif isinstance(name, (int, float)):
			return name # The "identifier" isn't actually an identifier, it's a literal!
		else:
			raise QSCOUTError("Unknown identifier %s" % str(name))
	for hs in p[1]:
		if hs[0] == 'let':
			c.let(hs[1], resolve_id(hs[2], {}, False))
		elif hs[0] == 'reg':
			c.reg(hs[1], resolve_id(hs[2], {}, False))
		elif hs[0] == 'map':
			if isinstance(hs[3], slice):
				c.map(hs[1], resolve_id(hs[2], {}, True), slice(resolve_id(hs[3].start, {}, False), resolve_id(hs[3].stop, {}, False), resolve_id(hs[3].step, {}, False)))
			else:
				c.map(hs[1], resolve_id(hs[2], {}, True), resolve_id(hs[3], {}, False))
	def process_statement(s, params = {}):
		if s[0] == 'loop':
			return LoopStatement(resolve_id(s[1], params, False), process_statement(s[2], params))
		elif s[0] == 'par':
			return GateBlock(True, [process_statement(x, params) for x in s[1]])
		elif s[0] == 'seq':
			return GateBlock(False, [process_statement(x, params) for x in s[1]])
		elif s[0] == 'gate':
			raw_args = s[2]
			args = []
			for arg in raw_args:
				if arg[0] == 'number':
					args.append(arg[1])
				elif arg[0] == 'id':
					args.append(resolve_id(arg[1], params))
				elif arg[0] == 'array':
					args.append(c.registers[arg[1][0]][resolve_id(arg[1][1], params, False)])
				else:
					print(s)
					raise QSCOUTError("Parse failed: unknown token %s" % str(arg[0]))
			return c.build_gate(s[1], *args)
		else:
			raise QSCOUTError("Parse failed: unknown token %s" % str(s[0]))
	
	for b in p[2]:
		if b[0] == 'macro':
			print(b)
			c.macro(b[1], b[2], process_statement(b[3], {param.name: param for param in b[2]}))
		else:
			c.gates.gates.append(process_statement(b))
	p[0] = c

def p_program_blanks(p):
	'program : EOL program'
	p[0] = p[2]

def p_header_statements(p):
	'header_statements : header_statement seq_sep header_statements'
	p[0] = [p[1]] + p[3]

def p_header_statements_s(p):
	'''header_statements : header_statement 
						 | header_statement seq_sep'''
	p[0] = [p[1]]

def p_header_statement(p):
	'''header_statement : register_statement
						| map_statement
						| let_statement'''
	p[0] = p[1]

def p_register_statement(p):
	'register_statement : REG array_declaration'
	p[0] = ('reg', p[2][0], p[2][1])

def p_map_statement(p):
	'map_statement : MAP map_target map_source'
	p[0] = ('map', p[2], p[3][0], p[3][1])

def p_map_target_id(p):
	'map_target : IDENTIFIER'
	p[0] = p[1]

# def p_map_target_array(p):
# 	'map_target : array_declaration'
# 	p[0] = p[1]

def p_map_source_id(p):
	'map_source : IDENTIFIER'
	p[0] = (p[1], None)

def p_map_source_array(p):
	'map_source : array_slice'
	p[0] = p[1]

def p_let_statement(p):
	'let_statement : LET IDENTIFIER number'
	p[0] = ('let', p[2], p[3])

def p_body_statements(p):
	'body_statements : body_statement seq_sep body_statements'
	p[0] = [p[1]] + p[3]

def p_body_statements_s(p):
	'''body_statements : body_statement
					   | body_statement seq_sep'''
	p[0] = [p[1]]

def p_body_statement(p):
	'''body_statement : gate_statement
					  | macro_definition
					  | loop_statement
					  | gate_block'''
	p[0] = p[1]

def p_gate_statement(p):
	'gate_statement : IDENTIFIER gate_arg_list'
	p[0] = ('gate', p[1], p[2])

def p_gate_arg_list(p):
	'gate_arg_list : gate_arg gate_arg_list'
	p[0] = [p[1]] + p[2]

def p_gate_arg_list_empty(p):
	'gate_arg_list : '
	p[0] = []

def p_gate_arg_array(p):
	'gate_arg : array_element'
	p[0] = ('array', p[1])

def p_gate_arg_id(p):
	'gate_arg : IDENTIFIER'
	p[0] = ('id', p[1])

def p_gate_arg_number(p):
	'gate_arg : number'
	p[0] = ('number', p[1])

def p_macro_definition(p):
	'macro_definition : MACRO IDENTIFIER gate_def_list gate_block'
	p[0] = ('macro', p[2], p[3], p[4])

def p_gate_def_list(p):
	'gate_def_list : IDENTIFIER gate_def_list'
	p[0] = [Parameter(p[1], None)] + p[2]

def p_gate_def_list_empty(p):
	'gate_def_list : '
	p[0] = []

def p_loop_statement(p):
	'loop_statement : LOOP let_or_integer gate_block'
	p[0] = ('loop', p[2], p[3])

def p_gate_block(p):
	'''gate_block : sequential_gate_block
				  | parallel_gate_block'''
	p[0] = p[1]

def p_sequential_gate_block(p):
	'sequential_gate_block : LBRACE sequential_statements RBRACE'
	p[0] = ('seq', p[2])

def p_sequential_gate_block_blanks(p):
	'sequential_gate_block : LBRACE EOL sequential_statements RBRACE'
	p[0] = ('seq', p[3])

def p_parallel_gate_block(p):
	'parallel_gate_block : LANGLE parallel_statements RANGLE'
	p[0] = ('par', p[2])

def p_parallel_gate_block_blanks(p):
	'parallel_gate_block : LANGLE EOL parallel_statements RANGLE'
	p[0] = ('par', p[3])

def p_sequential_statements(p):
	'sequential_statements : sequential_statement seq_sep sequential_statements'
	p[0] = [p[1]] + p[3]

def p_sequential_statements_s(p):
	'''sequential_statements : sequential_statement
							 | sequential_statement seq_sep'''
	p[0] = [p[1]]

def p_sequential_statement(p):
	'''sequential_statement : gate_statement
							| parallel_gate_block
							| loop_statement'''
	p[0] = p[1]

def p_parallel_statements(p):
	'parallel_statements : parallel_statement par_sep parallel_statements'
	p[0] = [p[1]] + p[3]

def p_parallel_statements_s(p):
	'''parallel_statements : parallel_statement
						   | parallel_statement par_sep'''
	p[0] = [p[1]]

def p_parallel_statement(p):
	'''parallel_statement : gate_statement
						  | sequential_gate_block'''
	p[0] = p[1]

def p_array_declaration(p):
	'array_declaration : IDENTIFIER LBRACKET let_or_integer RBRACKET'
	p[0] = (p[1], p[3])

def p_array_element(p):
	'array_element : IDENTIFIER LBRACKET let_or_integer RBRACKET'
	p[0] = (p[1], p[3])

def p_array_slice(p):
	'array_slice : IDENTIFIER LBRACKET slice_indexing RBRACKET'
	p[0] = (p[1], p[3])

def p_slice_indexing_one(p):
	'slice_indexing : let_or_integer'
	p[0] = p[1]

def p_slice_indexing_two(p):
	'slice_indexing : let_or_integer COLON let_or_integer'
	p[0] = slice(p[1], p[3])

def p_slice_indexing_three(p):
	'slice_indexing : let_or_integer COLON let_or_integer COLON let_or_integer'
	p[0] = slice(p[1], p[3], p[5])

def p_let_or_integer(p):
	'''let_or_integer : IDENTIFIER
					  | INTEGER'''
	p[0] = p[1]

def p_seq_sep(p):
	'''seq_sep : SEMICOLON
			   | EOL
			   | seq_sep EOL'''
	pass

def p_par_sep(p):
	'''par_sep : PIPE
			   | EOL
			   | par_sep EOL'''
	pass

def p_number(p):
	'''number : INTEGER
			  | FLOAT'''
	p[0] = p[1]

def parse_jaqal_string(jaqal):
	lexer = get_lexer()
	parser = yacc.yacc()
	return parser.parse(jaqal, lexer)
