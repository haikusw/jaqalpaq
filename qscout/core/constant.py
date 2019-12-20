from .parameter import AnnotatedValue, INT_TYPE, FLOAT_TYPE
from qscout import QSCOUTError

class Constant(AnnotatedValue):
	def __init__(self, name, value):
		if isinstance(value, Constant):
			super().__init__(self, name, value.kind)
		elif isinstance(value, float):
			super().__init__(self, name, FLOAT_TYPE)
		elif isinstance(value, int):
			super().__init__(self, name, INT_TYPE)
		else:
			raise QSCOUTError("Invalid/non-numeric value %s for constant %s!" % (value, name))
		self._value = value
	
	@property
	def value(self):
		return self._value
	
	def resolve_value(self, context={}):
		return self.value