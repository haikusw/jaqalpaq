import ply.lex as lex

tokens = ('REG', 'MAP', 'LET', 'MACRO', 'LOOP', 'LBRACE', 'RBRACE', 'LANGLE', 'RANGLE', 'LBRACKET', 'RBRACKET', 'COLON', 'EOL', 'LINECOMMENT', 'BLOCKCOMMENT', 'INTEGER', 'FLOAT', 'IDENTIFIER', 'SEMICOLON', 'PIPE')
reserved = {s: s.upper() for s in ('reg', 'map', 'let', 'macro', 'loop')}

def t_LINECOMMENT(t):
	r'//[^\n]*'
	pass

def t_BLOCKCOMMENT(t):
	r'/\*.*\*/'
	t.lexer.lineno += t.value.count('\n')

t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_LANGLE = r'<'
t_RANGLE = r'>'
t_LBRACKET = r'\['
t_RBRACKET = r'\]'
t_COLON = r':'
t_SEMICOLON = r';'
t_PIPE = r'\|'

def t_IDENTIFIER(t):
	r'[a-zA-Z_][a-zA-Z0-9_]*'
	t.type = reserved.get(t.value, 'IDENTIFIER')
	return t

def t_INTEGER(t):
	r'(([1-9]\d*)|0)(?![.eE])'
	t.value = int(t.value)
	return t

def t_FLOAT(t):
	r'(\+|-)?(([0-9]+(\.[0-9]*)?)|(\.[0-9]+))([eE][+-]?[0-9]*)?'
	t.value = float(t.value)
	return t

def t_EOL(t):
	r'\n|(\r\n)'
	t.lexer.lineno += 1
	return t

t_ignore = ' \t'

def t_error(t):
	print("Illegal input '%s'" % t.value)
	t.lexer.skip(1)

lexer = lex.lex()
