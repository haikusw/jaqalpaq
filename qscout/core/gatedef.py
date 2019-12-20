from .parameter import Parameter, QUBIT_TYPE, FLOAT_TYPE, REGISTER_TYPE
from qscout import QSCOUTError
from .gate import GateStatement

class AbstractGate:
	def __init__(self, name, parameters=None):
		self._name = name
		if parameters is None:
			self._parameters = []
		else:
			self._parameters = parameters
	
	@property
	def name(self):
		return self._name
	
	@property
	def parameters(self):
		return self._parameters
	
	def call(self, *args, **kwargs):
		if args and not kwargs:
			if len(args) > len(self.parameters):
				raise QSCOUTError("Too many parameters for gate %s." % self.name)
			elif len(args) > len(self.parameters):
				raise QSCOUTError("Insufficient parameters for gate %s." % self.name)
			else:
				params = dict(zip([param.name for param in self.parameters], args))
		elif kwargs and not args:
			if set(kwargs.keys()) != set([param.name for param in self.parameters]):
				raise QSCOUTError("Parameters %s do not match required parameters %s." % (str(kwargs.keys()), str([param.name for param in self.parameters])))
			else:
				params = kwargs
		elif kwargs and args:
			raise QSCOUTError("Cannot mix named and positional parameters in call to gate.")
		else:
			if not self.parameters:
				params = None
			else:
				raise QSCOUTError("Insufficient parameters for gate %s." % self.name)
		for name in params:
			self.parameters[name].validate(params[name])
		return GateStatement(self.name, params)

class GateDefinition(AbstractGate):
	pass

NATIVE_GATES = (
	GateDefinition('prepare_all'),
	GateDefinition('I', [Parameter('q', QUBIT_TYPE)]),
	GateDefinition('I2', [Parameter('q', QUBIT_TYPE)]),
	GateDefinition('R', [Parameter('q', QUBIT_TYPE), Parameter('axis-angle', FLOAT_TYPE), Parameter('rotation-angle', FLOAT_TYPE)]),
	GateDefinition('Rz', [Parameter('q', QUBIT_TYPE), Parameter('angle', FLOAT_TYPE)]),
	GateDefinition('Sx', [Parameter('q', QUBIT_TYPE)]),
	GateDefinition('Sy', [Parameter('q', QUBIT_TYPE)]),
	GateDefinition('Px', [Parameter('q', QUBIT_TYPE)]),
	GateDefinition('Py', [Parameter('q', QUBIT_TYPE)]),
	GateDefinition('MS', [Parameter('q1', QUBIT_TYPE), Parameter('q2', QUBIT_TYPE), Parameter('axis-angle', FLOAT_TYPE), Parameter('rotation-angle', FLOAT_TYPE)]),
	GateDefinition('XX', [Parameter('q1', QUBIT_TYPE), Parameter('q2', QUBIT_TYPE)]),
	GateDefinition('measure_all'),
)