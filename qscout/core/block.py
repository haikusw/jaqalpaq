class GateBlock:
	"""
	Represents a Jaqal block statement; either sequential or parallel. Can contain other
	blocks, loop statements, and gate statements.
	
	:param parallel: Set to False (default) for a sequential block, True for a parallel block, or None for an unscheduled block, which is treated as a sequential block except by the :mod:`qscout.scheduler` submodule.
	:type parallel: bool or None
	:param gates: The contents of the block.
	:type gates: list(GateStatement, LoopStatement, GateBlock)
	"""
	def __init__(self, parallel=False, gates=None):
		self.parallel = parallel
		if gates is None:
			self._gates = []
		else:
			self._gates = gates

	def __repr__(self):
		return f"GateBlock(parallel={self.parallel}, {self.gates})"

	def __eq__(self, other):
		try:
			return self.parallel == other.parallel and self.gates == other.gates
		except AttributeError:
			return False

	@property
	def gates(self):
		"""
		The contents of the block. In addition to read-only access through this property,
		a basic sequence protocol (``len()``, ``append()``, iteration, and indexing) is also
		supported to access the contents.
		"""
		return self._gates
	
	def __getitem__(self, key):
		return self.gates[key]
	
	def __setitem__(self, key, value):
		self.gates[key] = value
	
	def __delitem__(self, key):
		del self.gates[key]
	
	def __iter__(self):
		return iter(self.gates)
	
	def __len__(self):
		return len(self.gates)
	
	def append(self, instr):
		"""
		Adds an instruction to the end of the block.
		
		:param instr: The instruction to add.
		:type instr: GateStatement, LoopStatement, or GateBlock
		"""
		self.gates.append(instr)

class LoopStatement:
	"""
	Represents a Jaqal loop statement.
	
	:param int iterations: The number of times to repeat the loop.
	:param GateBlock gates: The block to repeat. If omitted, a new sequential block will be created.
	"""
	def __init__(self, iterations, gates=None):
		self.iterations = iterations
		if gates is None:
			self._gates = GateBlock()
		else:
			self._gates = gates
	
	@property
	def gates(self):
		"""
		The block that's repeated by the loop statement. In addition to read-only access
		through this property, the same basic sequence protocol (``len()``, ``append()``,
		iteration, and indexing) that the :class:`GateBlock` supports can also be used on
		the LoopStatement, and will be passed through.
		"""
		return self._gates

	def __getitem__(self, key):
		return self.gates[key]
	
	def __setitem__(self, key, value):
		self.gates[key] = value
	
	def __delitem__(self, key):
		del self.gates[key]
	
	def __iter__(self):
		return iter(self.gates)
	
	def __len__(self):
		return len(self.gates)
	
	def append(self, instr):
		"""
		Adds an instruction to the end of the repeated block.
		
		:param instr: The instruction to add.
		:type instr: GateStatement, LoopStatement, or GateBlock
		"""
		self.gates.append(instr)
