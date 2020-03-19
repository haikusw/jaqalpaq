from jaqalpup.core.circuit import ScheduledCircuit
from jaqalpup import QSCOUTError
from cirq import XXPowGate, XPowGate, YPowGate, ZPowGate, PhasedXPowGate, MeasurementGate
import numpy as np

CIRQ_NAMES = {
	XXPowGate: (lambda g, q1, q2: ('MS', q1, q2, 0, g.exponent * np.pi)),
	XPowGate: (lambda g, q: ('R', q, 0, g.exponent * np.pi)),
	YPowGate: (lambda g, q: ('R', q, 90.0, g.exponent * np.pi)),
	ZPowGate: (lambda g, q: ('Rz', q, g.exponent * np.pi)),
	PhasedXPowGate: (lambda g, q: ('R', q, g.phase_exponent * np.pi, g.exponent * np.pi))
}

def qscout_circuit_from_cirq_circuit(ccirc, names = None, native_gates = None):
	"""Converts a Cirq Circuit object to a :class:`qscout.core.ScheduledCircuit`.

	:param cirq.Circuit ccirc: The Circuit to convert.
	:returns: The same quantum circuit, converted to Jaqal-PUP.
	:rtype: ScheduledCircuit
	:raises QSCOUTError: if the input contains any instructions other than ``cirq.XXPowGate``, ``cirq.XPowGate``, ``cirq.YPowGate``, ``cirq.ZPowGate``, or ``cirq.PhasedXPowGate``.
	""" # TODO: Document this better.
	qcirc = ScheduledCircuit(native_gates is None)
	if native_gates is not None:
		qcirc.native_gates.update(native_gates)
	if names is None:
		names = CIRQ_NAMES
	try:
		n = 1 + max([qb.x for qb in ccirc.all_qubits()])
		line = True
	except:
		cqubits = ccirc.all_qubits()
		n = len(cqubits)
		qubitmap = {cqubits[i]: i for i in range(n)}
		line = False
	allqubits = qcirc.reg('allqubits', n)
	need_prep = True
	for moment in ccirc:
		if len(moment) == 0: continue
		if need_prep:
			qcirc.gate('prepare_all')
			need_prep = False
		if len(moment) == n and all([op.gate for op in moment]) and all([isinstance(op.gate, MeasurementGate) for op in moment]):
			qcirc.gate('measure_all')
			need_prep = True
			continue
		if len(moment) > 1:
			block = qcirc.block(parallel=True) # Note: If you tell Cirq you want MS gates in parallel, we'll generate a Jaqal file with exactly that, never mind that QSCOUT can't execute it.
		else:
			block = qcirc.body
		for op in moment:
			if op.gate:
				if type(op.gate) in names:
					if line:
						block.append(qcirc.build_gate(*names[type(op.gate)](op.gate, *[allqubits[qb.x] for qb in op.qubits])))
					else:
						block.append(qcirc.build_gate(*names[type(op.gate)](op.gate, *[allqubits[qubitmap[qb]] for qb in op.qubits])))
				else:
					raise QSCOUTError("Convert circuit to ion gates before compiling.")
			else:
				raise QSCOUTError("Cannot compile operation %s." % op)
	if not need_prep: # If we just measured, or the circuit is empty, don't add a final measurement.
		qcirc.gate('measure_all')
	return qcirc
