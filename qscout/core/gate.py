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
	
	def call(self, *args, **kwargs): # TODO: Validate that parameters have the correct types (qubit/number/?)
		if args and not kwargs:
			if len(args) > len(self.parameters):
				raise QSCOUTError("Too many parameters for gate %s." % self.name)
			elif len(args) > len(self.parameters):
				raise QSCOUTError("Insufficient parameters for gate %s." % self.name)
			else:
				return GateStatement(self.name, dict(zip([param.name for param in self.parameters], args)))
		elif kwargs and not args:
			if set(kwargs.keys()) != set([param.name for param in self.parameters]):
				raise QSCOUTError("Parameters %s do not match required parameters %s." % (str(kwargs.keys()), str([param.name for param in self.parameters])))
		elif kwargs and args:
			raise QSCOUTError("Cannot mix named and positional parameters in call to gate.")
		else:
			if not self.parameters:
				return GateStatement(self.name)
			else:
				raise QSCOUTError("Insufficient parameters for gate %s." % self.name)