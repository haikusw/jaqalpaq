from qscout import QSCOUTError

class Register:
	def __init__(self, name, size, alias_from=None, alias_slice=None):
		self._name = name
		self._size = size
		if (alias_from is None) != (alias_slice is None):
			raise QSCOUTError("Invalid register declaration: %s." % name)
		self._alias_from = alias_from
		self._alias_slice = alias_slice
		if alias_slice is not None: # TODO: Support let-expression parametrized slices
			start = alias_slice.start or 0
			step = alias_slice.step
			if step is None: step = 1
			if alias_slice.stop > alias_from.size:
				raise QSCOUTError("Index out of range.")
			if ((alias_slice.stop - start) // step) != size:
				raise QSCOUTError("Register %s declared size does not match actual size.")
		
	@property
	def name(self):
		return self._name
	
	@property
	def size(self):
		return self._size
	
	@property
	def fundamental(self):
		return self._alias_from is None
	
	@property
	def alias_from(self):
		return self._alias_from
	
	@property
	def alias_slice(self):
		return self._alias_slice
	
	def resolve_qubit(self, idx):
		if idx >= self.size:
			raise QSCOUTError("Index out of range.")
		if self.fundamental:
			return (self, idx)
		else:
			return self._alias_from.resolve_qubit(self.alias_slice.start + idx * self.alias_slice.step)
	
	def __getitem__(self, key):
		return NamedQubit(self.name + '[' + str(key) + ']', self, key)

class NamedQubit:
	def __init__(self, name, alias_from, alias_index):
		self._name = name
		self._alias_from = alias_from
		self._alias_index = alias_index # TODO: Support let-expression parametrized indices
		if alias_index >= alias_from.size:
			raise QSCOUTError("Index out of range.")
	
	@property
	def name(self):
		return self._name
	
	@property
	def fundamental(self):
		return False
	
	@property
	def alias_from(self):
		return self._alias_from
	
	@property
	def alias_index(self):
		return self._alias_index
	
	def resolve_qubit(self):
		return self._alias_from.resolve_qubit(self.alias_index)
	
	def renamed(self, name):
		return NamedQubit(name, self._alias_from, self._alias_index)