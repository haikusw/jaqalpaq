from jaqalpup import QSCOUTError

class GateStatement:
	"""
	Represents a Jaqal gate statement.
	
	:param GateDefinition gate_def: The gate to call.
	:param dict parameters: A map from gate parameter names to the values to pass for those parameters. Can be omitted for gates that have no parameters.
	"""
	def __init__(self, gate_def, parameters = None):
		self._gate_def = gate_def
		if parameters is None:
			self._parameters = {}
		else:
			self._parameters = parameters
	
	@property
	def name(self):
		return self._gate_def.name
	
	@property
	def gate_def(self):
		return self._gate_def
	
	@property
	def parameters(self):
		"""
		Read-only access to the dictionary mapping gate parameter names to the associated values.
		"""
		return self._parameters
	
	def moment_iter(self, parameters=None):
		yield [self]
