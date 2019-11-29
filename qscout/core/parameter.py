from qscout import QSCOUTError

QUBIT_PARAMETER = 'qubit'
FLOAT_PARAMETER = 'float'
PARAMETER_TYPES = (QUBIT_PARAMETER, FLOAT_PARAMETER, None)

class Parameter:
	def __init__(self, name, kind):
		self._name = name
		if kind not in PARAMETER_TYPES:
			raise QSCOUTError("Invalid parameter type specifier %s." % kind)
		self._kind = kind
	
	@property
	def name(self):
		return self._name
	
	@property
	def kind(self):
		return self._kind