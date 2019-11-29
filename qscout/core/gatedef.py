from .parameter import Parameter, QUBIT_PARAMETER, FLOAT_PARAMETER
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
	
	def call(self, *args, **kwargs): # TODO: Validate that parameters have the correct types (qubit/number/?)
		if args and not kwargs:
			if len(args) > len(self.parameters):
				raise QSCOUTError("Too many parameters for macro %s." % self.name)
			elif len(args) > len(self.parameters):
				raise QSCOUTError("Insufficient parameters for macro %s." % self.name)
			else:
				return GateStatement(self.name, dict(zip([param.name for param in self.parameters], args)))
		elif kwargs and not args:
			if set(kwargs.keys()) != set([param.name for param in self.parameters]):
				raise QSCOUTError("Parameters %s do not match required parameters %s." % (str(kwargs.keys()), str([param.name for param in self.parameters])))
		elif kwargs and args:
			raise QSCOUTError("Cannot mix named and positional parameters in call to macro.")
		else:
			if not self.parameters:
				return GateStatement(self.name)
			else:
				raise QSCOUTError("Insufficient parameters for macro %s." % self.name)

class GateDefinition(AbstractGate):
	pass

NATIVE_GATES = (
	GateDefinition('prepare_all'),
	GateDefinition('I', [Parameter('q', QUBIT_PARAMETER)]),
	GateDefinition('I2', [Parameter('q', QUBIT_PARAMETER)]),
	GateDefinition('R', [Parameter('q', QUBIT_PARAMETER), Parameter('axis-angle', FLOAT_PARAMETER), Parameter('rotation-angle', FLOAT_PARAMETER)]),
	GateDefinition('Rz', [Parameter('q', QUBIT_PARAMETER), Parameter('angle', FLOAT_PARAMETER)]),
	GateDefinition('Sx', [Parameter('q', QUBIT_PARAMETER)]),
	GateDefinition('Sy', [Parameter('q', QUBIT_PARAMETER)]),
	GateDefinition('Px', [Parameter('q', QUBIT_PARAMETER)]),
	GateDefinition('Py', [Parameter('q', QUBIT_PARAMETER)]),
	GateDefinition('MS', [Parameter('q1', QUBIT_PARAMETER), Parameter('q2', QUBIT_PARAMETER), Parameter('axis-angle', FLOAT_PARAMETER), Parameter('rotation-angle', FLOAT_PARAMETER)]),
	GateDefinition('XX', [Parameter('q1', QUBIT_PARAMETER), Parameter('q2', QUBIT_PARAMETER)]),
	GateDefinition('measure_all'),
)