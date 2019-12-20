from .block import GateBlock, LoopStatement
from .constant import Constant
from .gate import GateStatement
from .gatedef import GateDefinition, NATIVE_GATES
from .macro import Macro
from .register import Register, NamedQubit
from qscout import RESERVED_WORDS, QSCOUTError
import re

class ScheduledCircuit:
	def __init__(self, qscout_native_gates=False):
		self._constants = {}
		self._macros = {}
		self._native_gates = {}
		if qscout_native_gates:
			for gate in NATIVE_GATES:
				self._native_gates[gate.name] = gate
		self._registers = {}
		self._gates = GateBlock()
	
	@property
	def constants(self):
		return self._constants
	
	@property
	def macros(self):
		return self._macros
	
	@property
	def native_gates(self):
		return self._native_gates
	
	@property
	def registers(self):
		return self._registers
	
	@property
	def gates(self):
		return self._gates
	
	def fundamental_registers(self):
		return [r for r in self.registers.values() if r.fundamental]
	
	def used_qubit_indices(self, instr = None, context = {}}):
		if isinstance(instr, LoopStatement):
			return self.used_qubit_indices(self, instr.gates)
		
		indices = {r.name: set() for r in self.fundamental_registers}
		if instr is None: instr = self.gates
		
		if isinstance(instr, GateBlock):
			for sub_instr in instr:
				new_indices = self.used_qubit_indices(self, sub_instr)
				for k in new_indices:
					indices[k] |= new_indices[k]
		elif isinstance(instr, GateStatement):
			if instr.name in self.native_gates:
				for param_name in instr.parameters:
					param = instr.parameters[param_name]
					if isinstance(param, NamedQubit):
						reg, idx = param.resolve_qubit(context)
						indices[reg.name].add(idx)
					elif isinstance(param, Register):
						if param.size is not None:
							size = param.size
						else:
							size = param.resolve_size()
						for reg, idx in [param[i].resolve_qubit(context) for i in range(size)]:
							indices[reg.name].add(idx)
			elif instr.name in self.macros:
				return self.used_qubit_indices(self.macros[instr.name].gates, context + instr.parameters)
			else:
				raise QSCOUTError("Unknown gate %s." % instr.name)
		
		return indices
	
	def validate_identifier(self, name):
		if name in self.constants: return False
		if name in self.macros: return False
		if name in self.native_gates: return False
		if name in self.registers: return False
		if name in RESERVED_WORDS: return False
		if re.match('^[a-zA-Z_][a-zA-Z0-9_]*$', name): return True
		return False
	
	def let(self, name, value):
		if self.validate_identifier(name):
			self.constants[name] = Constant(name, value)
			return self.constants[name]
		else:
			raise QSCOUTError("Name %s already used or invalid." % name)
	
	def reg(self, name, size):
		if self.registers:
			raise QSCOUTError("Only one reg statement per program is permitted.")
		self.registers[name] = Register(name, size)
		return self.registers[name]
	
	def map(self, name, source=None, idxs=None):
		if self.validate_identifier(name):
			if source is None:
				raise QSCOUTError("Map statement for %s must have a source." % name)
			else:
				if source in self.registers:
					source_r = self.registers[source]
				elif source.name in self.registers and self.registers[source.name] == source:
					source_r = source
				else:
					raise QSCOUTError("Register %s does not exist." % source)
				if isinstance(source_r, NamedQubit):
					if idxs is None:
						self.registers[name] = source_r.renamed(name)
					else:
						raise QSCOUTError("Cannot index into single qubit %s." % source)
				else:
					if idxs is None:
						self.registers[name] = Register(name, alias_from=source_r)
					elif isinstance(idxs, slice):
						self.registers[name] = Register(name, alias_from=source_r, alias_slice=idxs)
					else:
						self.registers[name] = NamedQubit(name, source_r, idxs)
		else:
			raise QSCOUTError("Name %s already used or invalid." % name)
		return self.registers[name]
	
	def macro(self, name, parameters=None, body=None):
		if self.validate_identifier(name):
			if parameters is not None:
				for parameter in parameters:
					if (not self.validate_identifier(parameter.name)) or parameter.name == name:
						raise QSCOUTError("Name %s already used or invalid." % parameter.name)
			self.macros[name] = Macro(name, parameters, body)
			return self.macros[name]
		else:
			raise QSCOUTError("Name %s already used or invalid." % name)
	
	def build_gate(self, name, *args, **kwargs):
		if name in self.macros:
			return self.macros[name].call(*args, **kwargs)
		elif name in self.native_gates:
			return self.native_gates[name].call(*args, **kwargs)
		else:
			raise QSCOUTError("Unknown gate %s." % name)
	
	def gate(self, name, *args, **kwargs):
		g = self.build_gate(name, *args, **kwargs)
		self.gates.append(g)
		return g
	
	def block(self, parallel=False, gates=None):
		b = GateBlock(parallel, gates)
		self.gates.append(b)
		return b
	
	def loop(self, iterations, gates=None, parallel=False):
		# Parallel is ignored if a GateBlock is passed in; it's only used if building a GateBlock at the same time as the LoopStatement.
		# This is intentional, but may or may not be wise.
		if isinstance(gates, GateBlock):
			l = LoopStatement(iterations, gates)
		else:
			l = LoopStatement(iterations, GateBlock(parallel, gates))
		self.gates.append(l)
		return l