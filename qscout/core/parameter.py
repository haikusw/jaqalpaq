from qscout import QSCOUTError

QUBIT_TYPE = 'qubit'
FLOAT_TYPE = 'float'
REGISTER_TYPE = 'register'
INT_TYPE = 'int'
PARAMETER_TYPES = (QUBIT_TYPE, FLOAT_TYPE, REGISTER_TYPE, INT_TYPE, None)

class AnnotatedValue:
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
	
	def resolve_value(self, context={}):
		if self.name in context:
			return context[self.name]
		else:
			raise QSCOUTError("Unbound identifier %s." % alias_index.name)

class Parameter(AnnotatedValue):	
	def validate(self, value):
		from .register import NamedQubit, Register
		
		if self.kind == QUBIT_TYPE:
			if isinstance(value, NamedQubit):
				pass
			elif isinstance(value, AnnotatedValue) and value.kind in (QUBIT_TYPE, None):
				pass
			else:
				raise QSCOUTError("Type-checking failed: parameter %s=%s does not have type %s." % (str(self.name), str(value), str(self.kind)))
		elif self.kind == REGISTER_TYPE:
			if isinstance(value, Register):
				pass
			elif isinstance(value, AnnotatedValue) and value.kind in (REGISTER_TYPE, None):
				pass
			else:
				raise QSCOUTError("Type-checking failed: parameter %s=%s does not have type %s." % (str(self.name), str(value), str(self.kind)))
		elif self.kind == FLOAT_TYPE:
			if isinstance(value, float) or isinstance(value, int):
				pass
			elif isinstance(value, AnnotatedValue) and value.kind in (INT_TYPE, FLOAT_TYPE, None):
				pass
			else:
				raise QSCOUTError("Type-checking failed: parameter %s=%s does not have type %s." % (str(self.name), str(value), str(self.kind)))
		elif self.kind == INT_TYPE:
			if (isinstance(value, float) and int(value) == value) or isinstance(value, int):
				pass
			elif isinstance(value, AnnotatedValue) and value.kind in (INT_TYPE, None):
				pass
			else:
				raise QSCOUTError("Type-checking failed: parameter %s=%s does not have type %s." % (str(self.name), str(value), str(self.kind)))
		elif self.kind == None:
			# A parameter with kind None can take anything as input.
			# Such parameters are normally from user-defined macros, where there's no
			# ability to add type annotations in the Jaqal.
			pass
		else:
			raise QSCOUTError("Type-checking failed: unknown parameter type %s." + str(kind))
	
	def __getitem__(self, key):
		# Only makes sense for register parameters, but we'll let Register and NamedQubit do the typechecking.
		from .register import Register, NamedQubit
		if isinstance(key, slice):
			return Register(self.name + '[' + str(key) + ']', alias_from=self, alias_slice=key)
		else:
			return NamedQubit(self.name + '[' + str(key) + ']', self, key)
