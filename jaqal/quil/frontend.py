from jaqal.core import ScheduledCircuit
from jaqal import QSCOUTError
import networkx as nx
from pyquil.device import NxDevice
from pyquil.api import QuantumComputer
from .ioncompiler import IonCompiler
from .qscoutam import QSCOUTAM
import numpy as np

def get_ion_device(num_qubits):
	return NxDevice(nx.complete_graph(num_qubits))

def get_ion_qam():
	return QSCOUTAM()

def get_ion_qc(num_qubits):
	"""
	Constructs a quantum computer object that represents the QSCOUT hardware.
	Unlike the builtin Quil counterparts, it can't run quantum programs, but it can still
	be used as a compilation target and thus used to generate Jaqal code (which can then
	be submitted to be run on the actual QSCOUT device).
	
	:param int num_qubits: How many qubits in the trap will be used.
	:returns: The quantum computer object for compilation.
	:rtype: pyquil.api.QuantumComputer
	"""
	device = get_ion_device(num_qubits)
	return QuantumComputer(name="QSCOUT-%d" % num_qubits, qam=get_ion_qam(), device=device, compiler=IonCompiler(device))

def patch_simulator():
	"""
	Modifies pyquil's simulator to support trapped-ion gates. Run before attempting to
	simulate any circuit that includes R, SX, SY, or MS gates.
	
	.. warning::
		The simulator will give an error if R, SX, SY, or MS gates are passed to it before calling this function!
	"""
	from .gates import R, SX, SY, MS
	pyquil.gate_matrices.QUANTUM_GATES.update({'R': R, 'SX': SX, 'SY': SY, 'MS': MS})