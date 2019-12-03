from pyquil.api._qac import AbstractCompiler
from typing import Optional
from pyquil.quil import Program, Gate
from qscout.core import ScheduledCircuit
from qscout import QSCOUTError

QUIL_NAMES = {'I': 'I', 'R': 'R', 'SX': 'Sx', 'SY': 'Sy', 'X': 'Px', 'Y': 'Py', 'RZ': 'Rz', 'MS': 'MS'}

class IonCompiler(AbstractCompiler):
	def __init__(self, device):
		self._device = device
	def quil_to_native_quil(self, program: Program, *, protoquil=None) -> Program:
		return program # TODO: Implement native ion gates, transpiler pass to convert arbitrary circuit.
	
	def native_quil_to_executable(self, nq_program: Program) -> Optional[ScheduledCircuit]:
		n = max(nq_program.get_qubits()) + 1
		if n > len(self._device.qubits()):
			raise QSCOUTError("Program uses more qubits (%d) than device supports (%d)." % (n, len(self._device.qubits())))
		qsc = ScheduledCircuit(True) # TODO: Allow user to supply a different native gateset.
		qreg = qsc.reg('qreg', n)
		qsc.gate('prepare_all')
		for instr in nq_program:
			if isinstance(instr, Gate):
				if instr.name in QUIL_NAMES:
					qsc.gate(QUIL_NAMES[instr.name], *[qreg[qubit.index] for qubit in instr.qubits], *[float(p) for p in instr.params])
				else:
					raise QSCOUTError("Gate %s not in native gate set." % instr.name)
			else: # TODO: Support non-gate instructions
				raise QSCOUTError("Non-gate instruction %s not supported." % instr.out())
		qsc.gate('measure_all')
		return qsc