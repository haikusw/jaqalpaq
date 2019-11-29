from qscout import QSCOUTError

class GateStatement:
	def __init__(self, name, parameters = None):
		self.name = name
		if parameters is None:
			self._parameters = {}
		else:
			self._parameters = parameters
	
	@property
	def parameters(self):
		return self._parameters