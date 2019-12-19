from .parameter import Parameter, QUBIT_PARAMETER, FLOAT_PARAMETER
from qscout import QSCOUTError
from .gate import GateStatement
from .register import NamedQubit, Register

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
			kind = self.parameters[name].kind
			param = params[name]
			if kind == QUBIT_PARAMETER:
				if isinstance(param, NamedQubit):
					pass
				elif isinstance(param, Parameter) and param.kind in (QUBIT_PARAMETER, None):
					pass
				else:
					raise QSCOUTError("Type-checking failed: parameter %s=%s does not have type %s." % (str(name), str(param), str(kind)))
			elif kind == FLOAT_PARAMETER:
				if isinstance(param, float) or isinstance(param, int):
					pass
				elif isinstance(param, Parameter) and param.kind in (FLOAT_PARAMETER, None):
					pass
				else:
					raise QSCOUTError("Type-checking failed: parameter %s=%s does not have type %s." % (str(name), str(param), str(kind)))
			elif kind == None:
				# A parameter with kind None can take anything as input.
				# Such parameters are normally from user-defined macros, where there's no
				# ability to add type annotations in the Jaqal.
				pass
			else:
				raise QSCOUTError("Type-checking failed: unknown parameter type %s." + str(kind))
		return GateStatement(self.name, params)

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