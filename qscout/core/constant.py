class Constant:
	def __init__(self, name, value):
		self._name = name
		self._value = value
	
	@property
	def name(self):
		return self._name
	
	@property
	def value(self):
		return self._value