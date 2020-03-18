from .parameter import Parameter, QUBIT_TYPE, FLOAT_TYPE, REGISTER_TYPE
from jaqal import QSCOUTError
from .gate import GateStatement

class AbstractGate:
	"""
	The abstract base class for gate definitions. Everything here can be used whether the gate is defined by a macro in Jaqal, or is a gate defined by a pulse sequence in a gate definition file.
	
	:param str name: The name of the gate.
	:param parameters: What arguments (numbers, qubits, etc) the gate should be called with. If None, the gate takes no parameters.
	:type parameters: list(Parameter) or None
	"""
	def __init__(self, name, parameters=None):
		self._name = name
		if parameters is None:
			self._parameters = []
		else:
			self._parameters = parameters
	
	@property
	def name(self):
		"""
		The name of the gate.
		"""
		return self._name
	
	@property
	def parameters(self):
		"""
		What arguments (numbers, qubits, etc) the gate should be called with.
		"""
		return self._parameters
	
	def call(self, *args, **kwargs):
		"""
		Create a :class:`GateStatement` that calls this gate.
		The arguments to this method will be the arguments the gate is called with.
		If all arguments are keyword arguments, their names should match the names of this
		gate's parameters, and the values will be passed accordingly.
		If all arguments are positional arguments, each value will be passed to the next
		parameter in sequence.
		For convenience, calling the AbstractGate like a function is equivalent to this.
		
		:returns: The new statement.
		:rtype: GateStatement
		:raises QSCOUTError: If both keyword and positional arguments are passed.
		:raises QSCOUTError: If the wrong number of arguments are passed.
		:raises QSCOUTError: If the parameter names don't match the parameters this gate takes.
		"""
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
				params = {}
			else:
				raise QSCOUTError("Insufficient parameters for gate %s." % self.name)
		for name in params:
			for param in self.parameters:
				if param.name == name:
					param.validate(params[name])
					continue
			#raise QSCOUTError("Parameters %s do not match required parameters %s." % (str(kwargs.keys()), str([param.name for param in self.parameters])))
		return GateStatement(self.name, params)
	
	def __call__(self, *args, **kwargs):
		self.call(*args, **kwargs)

class GateDefinition(AbstractGate):
	"""
	Base: :class:`AbstractGate`
	
	Represents a gate that's implemented by a pulse sequence in a gate definition file.
	"""
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