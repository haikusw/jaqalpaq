from jaqal import QSCOUTError

class GateStatement:
	"""
	Represents a Jaqal gate statement.
	
	:param str name: The name of the gate to call.
	:param dict parameters: A map from gate parameter names to the values to pass for those parameters. Can be omitted for gates that have no parameters.
	"""
	def __init__(self, name, parameters = None):
		self.name = name
		if parameters is None:
			self._parameters = {}
		else:
			self._parameters = parameters
	
	@property
	def parameters(self):
		"""
		Read-only access to the dictionary mapping gate parameter names to the associated values.
		"""
		return self._parameters