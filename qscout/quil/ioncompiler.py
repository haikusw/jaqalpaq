from pyquil.api._qac import AbstractCompiler
from typing import Optional
from pyquil.quil import Program, Gate
from pyquil.quilbase import Measurement, ResetQubit, Reset
from qscout.core import ScheduledCircuit
from qscout import QSCOUTError
import numpy as np

QUIL_NAMES = {'I': 'I', 'R': 'R', 'SX': 'Sx', 'SY': 'Sy', 'X': 'Px', 'Y': 'Py', 'RZ': 'Rz', 'MS': 'MS'}

class IonCompiler(AbstractCompiler):
	"""
	A compiler that converts Quil programs to Jaqal circuits that can be executed on the QSCOUT device.
	
	:param pyquil.device.AbstractDevice device: The quantum device the compiler should target.
	"""
	
	def __init__(self, device):
		self._device = device
	def quil_to_native_quil(self, program: Program, *, protoquil=None) -> Program:
		"""
		Currently does nothing. Eventually, will compile a Quil program down to the native
		gates of the QSCOUT machine.
		
		:param pyquil.quil.Program program: The program to compile.
		:param bool protoquil: Ignored.
		:returns: The input program.
		:rtype: pyquil.quil.Program
		"""
		return program # TODO: Implement transpiler pass to convert arbitrary circuit.
	
	def native_quil_to_executable(self, nq_program: Program) -> Optional[ScheduledCircuit]:
		"""
		Compiles a Quil program to a :class:`qscout.core.ScheduledCircuit`. Because Quil
		does not support any form of schedule control, the entire circuit will be put in a
		single unscheduled block. If the :mod:`qscout.scheduler` is run on the circuit, as
		many as possible of those gates will be parallelized, while maintaining the order
		of gates that act on the same qubits. Otherwise, the circuit will be treated as a
		fully sequential circuit.
	
		Measurement and reset commands are supported, but only if applied to every qubit in
		the circuit in immediate succession. If so, they will be mapped to a prepare_all or
		measure_all gate. If the circuit does not end with a measurement, then a measure_all
		gate will be appended to it.
	
		:param pyquil.quil.Program nq_program: The program to compule.
		:returns: The same quantum program, converted to Jaqal-PUP.
		:rtype: qscout.core.ScheduledCircuit
		:raises QSCOUTError: If the program includes a non-gate instruction other than resets or measurements.
		:raises QSCOUTError: If the user tries to measure or reset only some of the qubits, rather than all of them.
		:raises QSCOUTError: If the program includes a gate other than I, R, SX, SY, X, Y, RZ, or MS.
		"""
		n = max(nq_program.get_qubits()) + 1
		if n > len(self._device.qubits()):
			raise QSCOUTError("Program uses more qubits (%d) than device supports (%d)." % (n, len(self._device.qubits())))
		qsc = ScheduledCircuit(True) # TODO: Allow user to supply a different native gateset.
		qsc.gates.parallel = None # Quil doesn't support barriers, so either the user
								  # won't run the the scheduler and everything will happen
								  # sequentially, or the user will and everything can be
								  # rescheduled as needed.
		qreg = qsc.reg('qreg', n)
		qsc.gate('prepare_all')
		reset_accumulator = set()
		measure_accumulator = set()
		for instr in nq_program:
			if reset_accumulator:
				if isinstance(instr, ResetQubit):
					reset_accumulator.add(instr.qubit.index)
					if nq_program.get_qubits() <= reset_accumulator:
						qsc.gate('prepare_all')
						reset_accumulator = {}
					continue
				else:
					raise QSCOUTError("Cannot reset only qubits %s and not whole register." % reset_accumulator)
					# reset_accumulator = set()
			if measure_accumulator:
				if isinstance(instr, Measurement):
					measure_accumulator.add(instr.qubit.index)
					if nq_program.get_qubits() <= measure_accumulator:
						qsc.gate('measure_all')
						measure_accumulator = {}
					continue
				else:
					raise QSCOUTError("Cannot measure only qubits %s and not whole register." % reset_accumulator)
					# measure_accumulator = set()
			if isinstance(instr, Gate):
				if instr.name in QUIL_NAMES:
					qsc.gate(QUIL_NAMES[instr.name], *[qreg[qubit.index] for qubit in instr.qubits], *[float(p) * 180 / np.pi for p in instr.params])
				else:
					raise QSCOUTError("Gate %s not in native gate set." % instr.name)
			elif isinstance(instr, Reset):
				if len(qsc.gates) > 1:
					qsc.gate('prepare_all')
			elif isinstance(instr, ResetQubit):
				if len(qsc.gates) > 1:
					reset_accumulator = {instr.qubit.index}
			elif isinstance(instr, Measurement):
				measure_accumulator = {instr.qubit.index} # We ignore the classical register.
			else:
				raise QSCOUTError("Instruction %s not supported." % instr.out())
		if qsc.gates[-1].name != 'measure_all':
			qsc.gate('measure_all')
		return qsc