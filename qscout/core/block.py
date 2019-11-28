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