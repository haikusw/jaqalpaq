from .parameter import AnnotatedValue, INT_TYPE, FLOAT_TYPE
from jaqal import QSCOUTError

class Constant(AnnotatedValue):
	"""
	Bases: :class:`qscout.core.AnnotatedValue`
	
	Represents a Jaqal let statement.
	
	:param str name: The name to bind the constant to.
	:param value: The numeric value to bind to that name; can be either a literal value or another Constant.
	:type value: Constant, int, or float
	"""
	def __init__(self, name, value):
		if isinstance(value, Constant):
			super().__init__(name, value.kind)
		elif isinstance(value, float):
			super().__init__(name, FLOAT_TYPE)
		elif isinstance(value, int):
			super().__init__(name, INT_TYPE)
		else:
			raise QSCOUTError("Invalid/non-numeric value %s for constant %s!" % (value, name))
		self._value = value
	
	@property
	def value(self):
		"""
		The fixed value of the constant.
		"""
		return self._value
	
	def resolve_value(self, context={}):
		"""
		Overrides: :meth:`qscout.core.AnnotatedValue.resolve_value`
		
		Unlike the superclass, ignores the context and simply returns the fixed value of
		the constant.
		"""
		return self.value