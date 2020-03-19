from jaqalpup.core import ScheduledCircuit, GateStatement
# from qscoutlib import MSGate, QasmGate, IonUnroller
from qiskit.converters import dag_to_circuit
from jaqalpup import QSCOUTError
#from sympy.core.evalf import N
import numpy as np

QISKIT_NAMES = {'i': 'I', 'r': 'R', 'sx': 'Sx', 'sy': 'Sy', 'x': 'Px', 'y': 'Py', 'rz': 'Rz', 'ms2': 'MS'}

def qscout_circuit_from_dag_circuit(dag):
	"""
	Converts a Qiskit directed-acyclic-graph representation of a circuit to a :class:`qscout.core.ScheduledCircuit`.
	See :func:`qscout_circuit_from_qiskit_circuit` for details.
	
	:param qiskit.dagcircuit.DAGCircuit dag: The directed acyclic graph circuit to convert.
	:returns: The same quantum circuit, converted to Jaqal-PUP.
	:rtype: qscout.core.ScheduledCircuit
	"""
	return qscout_circuit_from_qiskit_circuit(dag_to_circuit(dag))

def qscout_circuit_from_qiskit_circuit(circuit, names = None, native_gates = None):
	"""
	Converts a Qiskit circuit to a :class:`qscout.core.ScheduledCircuit`. The circuit will
	be structured into a sequence of unscheduled blocks. All instructions between one
	barrier statement and the next will be put into an unscheduled block together. If the 
	:mod:`qscout.scheduler` is run on the circuit, as many as possible of those gates will
	be parallelized within each block, while maintaining the order of the blocks.
	Otherwise, the circuit will be treated as a fully sequential circuit.
	
	Measurement and reset commands are supported, but only if applied to every qubit in
	the circuit in immediate succession. If so, they will be mapped to a prepare_all or
	measure_all gate. If the circuit does not end with a measurement, then a measure_all
	gate will be appended to it.
	
	Circuits containing multiple quantum registers will be converted to circuits with a
	single quantum register, containing all the qubits from each register. The parts of
	that larger register that correspond to each of the original registers will be mapped
	with the appropriate names.
	
	:param qiskit.circuit.QuantumCircuit dag: The circuit to convert.
	:param names: A mapping from names of Qiskit gates to the corresponding native Jaqal gate names.
		If omitted, maps i, r (:class:`qscout.qiskit.RGate`), sx (:class:`qscout.qiskit.SXGate`),
		sy (:class:`qscout.qiskit.SYGate`), x, y, rz, and ms2 (:class:`qscout.qiskit.MSGate`)
		to their QSCOUT counterparts.
	:type names: dict or None
	:param native_gates: The native gate set to target. If None, target the QSCOUT native gates.
	:type native_gates: dict or None
	:returns: The same quantum circuit, converted to Jaqal-PUP.
	:rtype: qscout.core.ScheduledCircuit
	:raises QSCOUTError: If any instruction acts on a qubit from a register other than the circuit's qregs.
	:raises QSCOUTError: If the circuit includes a snapshot instruction.
	:raises QSCOUTError: If the user tries to measure or reset only some of the qubits, rather than all of them.
	:raises QSCOUTError: If the circuit includes a gate not included in `names`.
	"""
	n = sum([qreg.size for qreg in circuit.qregs])
	qsc = ScheduledCircuit(native_gates is None)
	if native_gates is not None:
		qsc.native_gates.update(native_gates)
	if names is None:
		names = QISKIT_NAMES
	baseregister = qsc.reg('baseregister', n)
	offset = 0
	for qreg in circuit.qregs:
		qsc.map(qreg.name, baseregister, slice(offset, offset + qreg.size))
		offset += qreg.size
	qsc.gate('prepare_all')
	# We're going to divide the circuit up into blocks. Each block will contain every gate
	# between one barrier statement and the next. If the circuit is output with no further
	# processing, then the gates in each block will be run in sequence. However, if the
	# circuit is passed to the scheduler, it'll try to parallelize as many of the gates
	# within each block as possible, while keeping the blocks themselves sequential.
	block = qsc.block(parallel = None)
	measure_accumulator = set()
	reset_accumulator = set()
	for instr in circuit.data:
		if reset_accumulator:
			if instr[0].name == 'reset':
				target = instr[1][0]
				if target.register.name in qsc.registers:
					reset_accumulator.add(target.resolve_qubit(target.index)[1])
				else:
					raise QSCOUTError("Register %s invalid!" % target.register.name)
				if len(reset_accumulator) == n:
					qsc.gate('prepare_all')
					reset_accumulator = {}
				continue
			else:
				raise QSCOUTError("Cannot reset only qubits %s and not whole register." % reset_accumulator)
				# reset_accumulator = set()
		if measure_accumulator:
			if instr[0].name == 'measure':
				target = instr[1][0]
				if target.register.name in qsc.registers:
					measure_accumulator.add(target.resolve_qubit(target.index)[1])
				else:
					raise QSCOUTError("Register %s invalid!" % target.register.name)
				if len(measure_accumulator) == n:
					qsc.gate('measure_all')
					measure_accumulator = {}
				continue
			else:
				raise QSCOUTError("Cannot measure only qubits %s and not whole register." % reset_accumulator)
				# measure_accumulator = set()
		if instr[0].name == 'measure':
			target = instr[1][0]
			if target.register.name in qsc.registers:
				reset_accumulator = {target.resolve_qubit(target.index)[1]}
			else:
				raise QSCOUTError("Register %s invalid!" % target.register.name)
		elif instr[0].name == 'reset':
			if len(qsc.body) > 1:
				target = instr[1][0]
				if target.register.name in qsc.registers:
					reset_accumulator = {target.resolve_qubit(target.index)[1]}
				else:
					raise QSCOUTError("Register %s invalid!" % target.register.name)
		elif instr[0].name == 'barrier':
			block = qsc.block(parallel = None) # Use barriers to inform the scheduler, as explained above.
		elif instr[0].name == 'snapshot':
			raise QSCOUTError("Physical hardware does not support snapshot instructions.")
		elif instr[0].name in names:
			targets = instr[1]
			for target in targets:
				if target.register.name not in qsc.registers:
					raise QSCOUTError("Gate register %s invalid!" % target.register.name)
			block.append(qsc.build_gate(names[instr[0].name], *[qsc.registers[target.register.name][target.index] for target in targets], *[float(param) for param in instr[0].params]))
		else:
			raise QSCOUTError("Instruction %s not available on trapped ion hardware; try unrolling first." % instr[0].name)
	if not (isinstance(qsc.body[-1], GateStatement) and qsc.body[-1].name == 'measure_all'):
		qsc.gate('measure_all')
	return qsc
