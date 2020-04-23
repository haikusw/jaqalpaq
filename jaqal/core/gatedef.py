from collections import OrderedDict

from jaqal import QSCOUTError
from .gate import GateStatement

class AbstractGate:
	"""
	The abstract base class for gate definitions. Everything here can be used whether the gate is defined by a macro in Jaqal, or is a gate defined by a pulse sequence in a gate definition file.
	
	:param str name: The name of the gate.
	:param parameters: What arguments (numbers, qubits, etc) the gate should be called with. If None, the gate takes no parameters.
	:type parameters: list(Parameter) or None
	"""
	def __init__(self, name, parameters=None, ideal_action=None):
		self._name = name
		if parameters is None:
			self._parameters = []
		else:
			self._parameters = parameters
		self._ideal_action = ideal_action

	def __repr__(self):
		return f"{type(self).__name__}({self.name}, {self.parameters})"

	def __eq__(self, other):
		try:
			return self.name == other.name and self.parameters == other.parameters
		except AttributeError:
			return False

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
		params = OrderedDict()
		if args and not kwargs:
			if len(args) > len(self.parameters):
				raise QSCOUTError("Too many parameters for gate %s." % self.name)
			elif len(args) > len(self.parameters):
				raise QSCOUTError("Insufficient parameters for gate %s." % self.name)
			else:
				for name,arg in zip([param.name for param in self.parameters], args):
					params[name] = arg
		elif kwargs and not args:
			try:
				for param in self.parameters:
					params[param.name] = kwargs.pop(param.name)
			except KeyError as ex:
				raise QSCOUTError(f"Missing parameter {param.name} for gate {self.name}.") from ex
			if kwargs:
				raise QSCOUTError(f"Invalid parameters {', '.join(kwargs)} for gate {self.name}.")
		elif kwargs and args:
			raise QSCOUTError("Cannot mix named and positional parameters in call to gate.")
		if len(self.parameters) != len(params):
			raise QSCOUTError(f"Bad argument count: expected {len(self.parameters)}, found {len(params)}")
		for param in self.parameters:
			param.validate(params[param.name])
		return GateStatement(self, params)

	def __call__(self, *args, **kwargs):
		return self.call(*args, **kwargs)

class GateDefinition(AbstractGate):
	"""
	Base: :class:`AbstractGate`
	
	Represents a gate that's implemented by a pulse sequence in a gate definition file.
	"""
	pass
