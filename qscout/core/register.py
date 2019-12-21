from qscout import QSCOUTError
from .parameter import AnnotatedValue, Parameter, INT_TYPE, REGISTER_TYPE
from .constant import Constant

class Register:
	def __init__(self, name, size=None, alias_from=None, alias_slice=None):
		self._name = name
		self._size = size
		if (alias_from is None) and not (alias_slice is None and size is not None):
			raise QSCOUTError("Invalid register declaration: %s." % name)
		if (size is not None) and (alias_from is not None):
			raise QSCOUTError("Illegal size specification in map statement defining %s." % name)
		self._alias_from = alias_from
		self._alias_slice = alias_slice
		if alias_slice is not None:
			if isinstance(alias_slice.start, AnnotatedValue) or isinstance(alias_slice.stop, AnnotatedValue) or isinstance(alias_slice.step, AnnotatedValue) or isinstance(alias_from, AnnotatedValue):
				# Verify that the Parameters given have the correct types
				if isinstance(alias_slice.start, AnnotatedValue) and alias_slice.start.kind not in (INT_TYPE, None):
					raise QSCOUTError("Cannot slice register %s with parameter %s of non-integer kind %s." % (alias_from.name, alias_slice.start.name, alias_slice.start.kind))
				elif isinstance(alias_slice.stop, AnnotatedValue) and alias_slice.stop.kind not in (INT_TYPE, None):
					raise QSCOUTError("Cannot slice register %s with parameter %s of non-integer kind %s." % (alias_from.name, alias_slice.stop.name, alias_slice.stop.kind))
				elif isinstance(alias_slice.step, AnnotatedValue) and alias_slice.step.kind not in (INT_TYPE, None):
					raise QSCOUTError("Cannot slice register %s with parameter %s of non-integer kind %s." % (alias_from.name, alias_slice.step.name, alias_slice.step.kind))
				elif isinstance(alias_from, AnnotatedValue) and alias_from.kind not in (REGISTER_TYPE, None):
					raise QSCOUTError("Cannot slice parameter %s of non-register kind %s." % (alias_from.name, alias_from.kind))
			elif alias_from.size is not None and not isinstance(alias_from.size, AnnotatedValue):
				if alias_slice.stop > alias_from.size:
					raise QSCOUTError("Index out of range.")
	
	@property
	def name(self):
		return self._name
	
	@property
	def size(self):
		if self._size is not None:
			return self._size
		
		alias_from = self.alias_from
		while isinstance(alias_from, AnnotatedValue):
			alias_from.resolve_value(context)
		if self.alias_slice is None:
			return self.alias_from.size
		
		start = self.alias_slice.start or 0
		step = self.alias_slice.step
		if step is None: step = 1
		stop = self.alias_slice.stop
		while isinstance(start, AnnotatedValue):
			start.resolve_value(context)
		while isinstance(step, AnnotatedValue):
			step.resolve_value(context)
		while isinstance(stop, AnnotatedValue):
			stop.resolve_value(context)
		return ((stop - start) // step)
	
	@property
	def fundamental(self):
		return self.alias_from is None
	
	@property
	def alias_from(self):
		return self._alias_from
	
	@property
	def alias_slice(self):
		return self._alias_slice
	
	def resolve_qubit(self, idx, context={}):
		if self.size is not None and idx >= self.size:
			raise QSCOUTError("Index out of range.")
		if self.fundamental:
			return (self, idx)
		start = self.alias_slice.start or 0
		step = self.alias_slice.step
		if step is None: step = 1
		alias_from = self.alias_from
		while isinstance(start, AnnotatedValue):
			start.resolve_value(context)
		while isinstance(step, AnnotatedValue):
			step.resolve_value(context)
		while isinstance(alias_from, AnnotatedValue):
			alias_from.resolve_value(context)
		return alias_from.resolve_qubit(start + idx * step, context)
	
	def __getitem__(self, key):
		if isinstance(key, slice):
			raise QSCOUTError("Anonymous slices are not currently supported; slice only in a map statement.")
			# But if the backend ever supports it, just replace the above line with the below line:
			# return Register(self.name + '[' + str(key) + ']', alias_from=self, alias_slice=key)
		else:
			return NamedQubit(self.name + '[' + str(key) + ']', self, key)

class NamedQubit:
	def __init__(self, name, alias_from, alias_index):
		self._name = name
		self._alias_from = alias_from
		self._alias_index = alias_index
		if alias_index is None or alias_from is None:
			raise QSCOUTError("Invalid map statement constructing qubit %s." % name)
		if isinstance(alias_index, AnnotatedValue) or isinstance(alias_from, AnnotatedValue):
				if isinstance(alias_index, AnnotatedValue) and alias_index.kind not in (INT_TYPE, None):
					raise QSCOUTError("Cannot slice register %s with parameter %s of non-integer kind %s." % (alias_from.name, alias_index.name, alias_index.kind))
				if isinstance(alias_from, AnnotatedValue) and alias_from.kind not in (REGISTER_TYPE, None):
					raise QSCOUTError("Cannot slice parameter %s of non-register kind %s." % (alias_from.name, alias_from.kind))
		elif alias_index >= alias_from.size:
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
	
	def resolve_qubit(self, context={}):
		alias_index = self.alias_index
		alias_from = self.alias_from
		while isinstance(alias_index, AnnotatedValue):
			alias_index = alias_index.resolve_value(context)
		while isinstance(alias_from, AnnotatedValue):
			alias_from = alias_from.resolve_value(context)
		return alias_from.resolve_qubit(alias_index, context)
	
	def renamed(self, name):
		return NamedQubit(name, self.alias_from, self.alias_index)