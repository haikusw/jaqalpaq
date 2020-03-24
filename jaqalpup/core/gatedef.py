from collections import OrderedDict
import numpy as np

from .parameter import Parameter, QUBIT_TYPE, FLOAT_TYPE, REGISTER_TYPE
from jaqalpup import QSCOUTError
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
		for param in self.parameters:
			param.validate(params[param.name])
		return GateStatement(self, params)
	
	def __call__(self, *args, **kwargs):
		self.call(*args, **kwargs)

class GateDefinition(AbstractGate):
	"""
	Base: :class:`AbstractGate`
	
	Represents a gate that's implemented by a pulse sequence in a gate definition file.
	"""
	pass

def R_unitary(theta, phi):
	"""
	Generates the unitary matrix that describes the QSCOUT native R gate, which performs
	an arbitrary rotation around an axis in the X-Y plane.
	
	:param float theta: The angle that sets the planar axis to rotate around.
	:param float phi: The angle by which the gate rotates the state.
	:returns: The unitary gate matrix.
	:rtype: numpy.array
	"""
	return np.array([[np.cos(phi / 2.0), (-1j * np.cos(theta) - np.sin(theta)) * np.sin(phi / 2.0)],
					[(-1j * np.cos(theta) + np.sin(theta)) * np.sin(phi / 2.0), np.cos(phi / 2.0)]])

def MS_unitary(theta, phi):
	"""
	Generates the unitary matrix that describes the QSCOUT native Mølmer-Sørensen gate.
	This matrix is equivalent to ::
	
		exp(-i theta/2 (cos(phi) XI + sin(phi) YI) (cos(phi) IX + sin(phi) IY))
		
	:param float theta: The angle by which the gate rotates the state.
	:param float phi: The phase angle determining the mix of XX and YY rotation.
	:returns: The unitary gate matrix.
	:rtype: numpy.array
	"""
	return np.array([[np.cos(theta/2.0), 0, 0, -1j * (np.cos(phi * 2.0) - 1j * np.sin(phi * 2.0)) * np.sin(theta/2.0)],
					[0, np.cos(theta/2.0), -1j * np.sin(theta/2.0), 0],
					[0, -1j * np.sin(theta/2.0), np.cos(theta/2.0), 0],
					[-1j * (np.cos(phi * 2.0) - 1j * np.sin(phi * 2.0)) * np.sin(theta/2.0), 0, 0, np.cos(theta/2.0)]])

def RX_unitary(phi):
	return np.array([[np.cos(phi/2), -1j*np.sin(phi/2)],
					[-1j*np.sin(phi/2), np.cos(phi/2)]])

def RY_unitary(phi):
	return np.array([[np.cos(phi/2), -np.sin(phi/2)],
					[np.sin(phi/2), np.cos(phi/2)]])

def RZ_unitary(phi):
	return np.array([[1, 0],
					[0, np.exp(1j*phi)]])

NATIVE_GATES = (
	GateDefinition('prepare_all'),
	GateDefinition('R', [Parameter('q', QUBIT_TYPE), Parameter('axis-angle', FLOAT_TYPE), Parameter('rotation-angle', FLOAT_TYPE)],
					ideal_action=R_unitary),
	GateDefinition('Rx', [Parameter('q', QUBIT_TYPE), Parameter('angle', FLOAT_TYPE)],
					ideal_action=RX_unitary),
	GateDefinition('Ry', [Parameter('q', QUBIT_TYPE), Parameter('angle', FLOAT_TYPE)],
					ideal_action=RY_unitary),
	GateDefinition('Rz', [Parameter('q', QUBIT_TYPE), Parameter('angle', FLOAT_TYPE)],
					ideal_action=RZ_unitary),
	GateDefinition('Px', [Parameter('q', QUBIT_TYPE)],
					ideal_action=lambda: RX_unitary(np.pi)),
	GateDefinition('Py', [Parameter('q', QUBIT_TYPE)],
					ideal_action=lambda: RY_unitary(np.pi)),
	GateDefinition('Pz', [Parameter('q', QUBIT_TYPE)],
					ideal_action=lambda: RZ_unitary(np.pi)),
	GateDefinition('Sx', [Parameter('q', QUBIT_TYPE)],
					ideal_action=lambda: RX_unitary(np.pi/2)),
	GateDefinition('Sy', [Parameter('q', QUBIT_TYPE)],
					ideal_action=lambda: RY_unitary(np.pi/2)),
	GateDefinition('Sz', [Parameter('q', QUBIT_TYPE)],
					ideal_action=lambda: RZ_unitary(np.pi/2)),
	GateDefinition('Sxd', [Parameter('q', QUBIT_TYPE)],
					ideal_action=lambda: RX_unitary(-np.pi/2)),
	GateDefinition('Syd', [Parameter('q', QUBIT_TYPE)],
					ideal_action=lambda: RY_unitary(-np.pi/2)),
	GateDefinition('Szd', [Parameter('q', QUBIT_TYPE)],
					ideal_action=lambda: RZ_unitary(-np.pi/2)),
	GateDefinition('MS', [Parameter('q1', QUBIT_TYPE), Parameter('q2', QUBIT_TYPE), Parameter('axis-angle', FLOAT_TYPE), Parameter('rotation-angle', FLOAT_TYPE)],
					ideal_action=MS_unitary),
	GateDefinition('Sxx', [Parameter('q1', QUBIT_TYPE), Parameter('q2', QUBIT_TYPE)],
					ideal_action=lambda: MS_unitary(np.pi,0)),
	GateDefinition('measure_all'),
)
