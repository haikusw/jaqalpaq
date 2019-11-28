from .block import GateBlock
from .gate import GateStatement
from .gatedef import AbstractGate
from qscout import QSCOUTError

class Macro(AbstractGate):
	def __init__(self, name, parameters=None, body=None):
		super().__init__(name, parameters)
		if body is None:
			self._body = GateBlock()
		else:
			self._body = body
	
	@property
	def body(self):
		return self._body