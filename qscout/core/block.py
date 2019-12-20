class GateBlock:
	def __init__(self, parallel=False, gates=None):
		self.parallel = parallel
		if gates is None:
			self._gates = []
		else:
			self._gates = gates
	
	@property
	def gates(self):
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
		self.gates.append(instr)

class LoopStatement:
	def __init__(self, iterations, gates=None):
		self.iterations = iterations
		if gates is None:
			self._gates = GateBlock()
		else:
			self._gates = gates
	
	@property
	def gates(self):
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
		self.gates.append(instr)
