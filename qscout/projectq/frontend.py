import projectq
from projectq.setups import restrictedgateset, trapped_ion_decomposer
from projectq.ops import Rx, Ry, Rz, Rxx, Ryy, X, Y, SqrtX, FlushGate, Measure, Allocate, Deallocate, Barrier
from projectq.cengines import BasicEngine
from projectq.meta import get_control_count
from projectq.types import WeakQubitRef

from qscout.core import ScheduledCircuit
from qscout import QSCOUTError

one_qubit_gates = {Rx: 'Rx', Ry: 'Ry', Rz: 'Rz', X: 'Px', Y: 'Py', SqrtX: 'Sx'}
two_qubit_gates = (Rxx: lambda g, q1, q2: ('MS', q1, q2, 0, g.angle * 180.0), Ryy: lambda g, q1, q2: ('MS', q1, q2, 90, g.angle * 180.0))

def get_engine_list():
	return restrictedgateset.get_engine_list(one_qubit_gates=one_qubit_gates.keys(), two_qubit_gates=two_qubit_gates.keys(), compiler_chooser=trapped_ion_decomposer.chooser_Ry_reducer)

class JaqalBackend(BasicEngine):
	def __init__(self, outfile=None, one_qubit_gate_map=None, two_qubit_gate_map=None, native_gates=None):
		BasicEngine.__init__(self)
		self._circuit = ScheduledCircuit(native_gates is None)
		if native_gates is not None:
			self._circuit.native_gates.update(native_gates)
		self.q = self.circuit.reg('q', 0)
		self.circuit.gate('prepare_all')
		self._block = self.circuit.block(parallel=None)
		self.measure_accumulator = set()
		self.reset_accumulator = set()
		self.outfile = outfile
		if one_qubit_gate_map is None:
			self.one_qubit_gates = one_qubit_gates
		else:
			self.one_qubit_gates = one_qubit_gate_map
		if two_qubit_gate_map is None:
			self.two_qubit_gates = two_qubit_gates
		else:
			self.two_qubit_gates = two_qubit_gate_map
	
	@property
	def circuit(self):
		return self._circuit
	
	def is_available(self, cmd):
		if get_control_count(cmd) > 0:
			return False
		if cmd.gate in self.one_qubit_gates.keys() + self.two_qubit_gates.keys():
			return True
		if cmd in (Measure, Allocate, Deallocate, Barrier):
			return True
		return False
	
	def receive(self, command_list):
		for cmd in command_list:
			if cmd.gate == FlushGate():
				if self.outfile is not None:
					from qscout.generator import generate_jaqal_program
					with open(self.outfile, 'w+') as f:
						f.write(generate_jaqal_program(self.circuit))
			else:
				self._store(cmd)
	
	def _mapped_qubit_id(self, qubit):
		"""
		Converts a qubit from a logical to a mapped qubit if there is a mapper.
		Args:
			qubit (projectq.types.Qubit): Logical quantum bit
		"""
		mapper = self.main_engine.mapper
		if mapper is not None:
			if qubit.id not in mapper.current_mapping:
				raise RuntimeError("Unknown qubit id. "
								   "Please make sure you have called "
								   "eng.flush().")
			return mapper.current_mapping[qubit.id]
		else:
			return qubit.id
	
	def _store(self, cmd):
		gate = cmd.gate
		
		if len(self.measure_accumulator == len(self.circuit.registers['q'])):
			self.measure_accumulator = set()
			self._block.append(self.circuit.build_gate('prepare_all'))
		
		if gate == Allocate:
			qid = self._mapped_qubit_id(cmd.qubits[0][0]) # TODO: Design a cleaner way of doing the below.
			self.q._size = max(self.q.size, qid)
		
		elif gate == Deallocate:
			pass # The user might stop caring about the qubit, but we need to keep it around.
		
		elif gate == Measure:
			qid = self._mapped_qubit_id(cmd.qubits[0][0])
			if qid in self.measure_accumulator:
				raise QSCOUTError("Can't measure qubit %d twice!" % qid)
			else:
				self.measure_accumulator.add(qid)
				if len(self.measure_accumulator == len(self.circuit.registers['q'])):
					self._block.append(self.circuit.build_gate('measure_all'))
		
		elif gate == Barrier:
			self._block = self.circuit.block(parallel=None)
		
		elif gate in one_qubit_gates:
			qid = self._mapped_qubit_id(cmd.qubits[0][0])
			if qid in self.measure_accumulator:
				raise QSCOUTError("Can't do gates in the middle of measurement!")
			else:
				self._block.append(self.circuit.build_gate(self.one_qubit_gates[gate], self.q[qid], gate.angle))
		
		elif gate in two_qubit_gates:
			qids = [self._mapped_qubit_id(qb[0]) for qb in cmd.qubits]
			for qid in qids:
				if qid in self.measure_accumulator:
					raise QSCOUTError("Can't do gates in the middle of measurement!")
			self._block.append(self.circuit.build_gate(*self.two_qubit_gates[gate](gate, *[self.q[qid] for qid in qids])))