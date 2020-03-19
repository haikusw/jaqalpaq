from pytket.circuit import OpType

from jaqalpup.core import ScheduledCircuit, BlockStatement

import numpy as np

from jaqalpup import QSCOUTError

TKET_NAMES = {OpType.PhasedX: lambda q, alpha, beta: ('R', q, alpha, -beta), OpType.Rz: lambda q, theta: ('Rz', q, theta), OpType.XXPhase: lambda q1, q2, theta: ('MS', q1, q2, 0, theta)}

def qscout_circuit_from_tket_circuit(tkc, native_gates = None, names = None):
	qreg_sizes = {}
	for qb in tkc.qubits:
		if len(qb.index) != 1:
			qreg_sizes[qb.reg_name + '_'.join([str(x) for x in qb.index])] = 1
		elif qb.reg_name in qreg_sizes:
			qreg_sizes[qb.reg_name] = max(qreg_sizes[qb.reg_name], qb.index[0] + 1)
		else:
			qreg_sizes[qb.reg_name] = qb.index[0] + 1
	n = sum(qreg_sizes.values())
	qsc = ScheduledCircuit(native_gates is None)
	if native_gates is not None:
		qsc.native_gates.update(native_gates)
	if names is None:
		names = TKET_NAMES
	baseregister = qsc.reg('baseregister', n)
	offset = 0
	for qreg in qreg_sizes:
		qsc.map(qreg, baseregister, slice(offset, offset + qreg_sizes[qreg]))
		offset += qreg_sizes[qreg]
	qsc.gate('prepare_all')
	# We're going to divide the circuit up into blocks. Each block will contain every gate
	# between one barrier statement and the next. If the circuit is output with no further
	# processing, then the gates in each block will be run in sequence. However, if the
	# circuit is passed to the scheduler, it'll try to parallelize as many of the gates
	# within each block as possible, while keeping the blocks themselves sequential.
	block = qsc.block(parallel = None)
	measure_accumulator = set()
	for command in tkc:
		block, measure_accumulator = convert_command(command, qsc, block, names, measure_accumulator, n)
	if qsc.body[-1][-1].name != 'measure_all':
		qsc.gate('measure_all')
	return qsc

def convert_command(command, qsc, block, names, measure_accumulator, n, remaps = None):
	if remaps is None: remaps = range(n)
	op_type = command.op.get_type()
	if measure_accumulator:
		if op_type == OpType.Measure:
			target = command.qubits[0]
			if target.reg_name in qsc.registers:
				measure_accumulator.add(target.resolve_qubit(target.index)[1])
			else:
				raise QSCOUTError("Register %s invalid!" % target.register.name)
			if len(measure_accumulator) == n:
				block.append(qsc.build_gate('measure_all'))
				measure_accumulator = set()
			return block, measure_accumulator
		else:
			raise QSCOUTError("Cannot measure only qubits %s and not whole register." % measure_accumulator)
			# measure_accumulator = set()
	if op_type == OpType.Measure:
		qb = command.qubits[0]
		if len(qb.index) != 1:
			target = qsc.registers[qb.reg_name + '_'.join([str(x) for x in qb.index])][0]
		else:
			target = qsc.registers[qb.reg_name][qb.index[0]]
		measure_accumulator = {target.resolve_qubit()[1]}
	elif op_type == OpType.Barrier:
		block = qsc.block(parallel = None) # Use barriers to inform the scheduler, as explained above.
	elif op_type in (OpType.CircBox, OpType.ExpBox, OpType.PauliExpBox):
		new_remaps = [remaps[qb.index[0]] for qb in command.qubits]
		macro_block = BlockStatement()
		subcirq = command.op.get_circuit()
		for cmd in subcirq:
			convert_command(cmd, qsc, macro_block, names, set(), n, new_remaps)
		macro_name = f'macro_{len(qsc.macros)}'
		qsc.macro(macro_name, [], macro_block)
		block.append(qsc.build_gate(macro_name))
		# TODO: Re-use macros when the same circuit block appears in multiple places.
	elif op_type in names:
		targets = command.qubits
		qb_targets = []
		for qb in targets:
			if len(qb.index) != 1: # TODO: Figure out how to pass multi-index qubits in macros.
				qb_targets.append(qsc.registers[qb.reg_name + '_'.join([str(x) for x in qb.index])][0])
			else:
				qb_targets.append(qsc.registers[qb.reg_name][remaps[qb.index[0]]])
		block.append(qsc.build_gate(*names[op_type](*qb_targets, *[float(param) * np.pi for param in command.op.get_params()])))
	else:
		raise QSCOUTError("Instruction %s not available on trapped ion hardware; try unrolling first." % op_type)
	return block, measure_accumulator
