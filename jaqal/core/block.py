class BlockStatement:
	"""
	Represents a Jaqal block statement; either sequential or parallel. Can contain other
	blocks, loop statements, and gate statements.
	
	:param parallel: Set to False (default) for a sequential block, True for a parallel block, or None for an unscheduled block, which is treated as a sequential block except by the :mod:`qscout.scheduler` submodule.
	:type parallel: bool or None
	:param statements: The contents of the block.
	:type statements: list(GateStatement, LoopStatement, BlockStatement)
	"""
	def __init__(self, parallel=False, statements=None):
		self.parallel = parallel
		if statements is None:
			self._statements = []
		else:
			self._statements = statements

	def __repr__(self):
		return f"BlockStatement(parallel={self.parallel}, {self.statements})"

	def __eq__(self, other):
		try:
			return self.parallel == other.parallel and self.statements == other.statements
		except AttributeError:
			return False

	@property
	def statements(self):
		"""
		The contents of the block. In addition to read-only access through this property,
		a basic sequence protocol (``len()``, ``append()``, iteration, and indexing) is also
		supported to access the contents.
		"""
		return self._statements
	
	def __getitem__(self, key):
		return self.statements[key]
	
	def __setitem__(self, key, value):
		self.statements[key] = value
	
	def __delitem__(self, key):
		del self.statements[key]
	
	def __iter__(self):
		return iter(self.statements)
	
	def __len__(self):
		return len(self.statements)
	
	def append(self, instr):
		"""
		Adds an instruction to the end of the block.
		
		:param instr: The instruction to add.
		:type instr: GateStatement, LoopStatement, or BlockStatement
		"""
		self.statements.append(instr)

class LoopStatement:
	"""
	Represents a Jaqal loop statement.
	
	:param int iterations: The number of times to repeat the loop.
	:param BlockStatement gates: The block to repeat. If omitted, a new sequential block will be created.
	"""
	def __init__(self, iterations, statements=None):
		self.iterations = iterations
		if statements is None:
			self._statements = BlockStatement()
		else:
			self._statements = statements

	def __repr__(self):
		return f"LoopStatement({self.iterations}, {self.statements})"

	def __eq__(self, other):
		try:
			return self.iterations == other.iterations and self.statements == other.statements
		except AttributeError:
			return False

	@property
	def statements(self):
		"""
		The block that's repeated by the loop statement. In addition to read-only access
		through this property, the same basic sequence protocol (``len()``, ``append()``,
		iteration, and indexing) that the :class:`BlockStatement` supports can also be used on
		the LoopStatement, and will be passed through.
		"""
		return self._statements

	def __getitem__(self, key):
		return self.statements[key]
	
	def __setitem__(self, key, value):
		self.statements[key] = value
	
	def __delitem__(self, key):
		del self.statements[key]
	
	def __iter__(self):
		return iter(self.statements)
	
	def __len__(self):
		return len(self.statements)
	
	def append(self, instr):
		"""
		Adds an instruction to the end of the repeated block.
		
		:param instr: The instruction to add.
		:type instr: GateStatement, LoopStatement, or BlockStatement
		"""
		self.statements.append(instr)
