from jaqalpup.core import ScheduledCircuit
from jaqalpup.core.gatedef import NATIVE_GATES
from jaqalpup import QSCOUTError
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
	simulate any circuit that includes the QSCOUT native gates.
	
	.. warning::
		The simulator will give an error if QSCOUT native gates are passed to it before calling this function!
	"""
	dkt = {}
	for gate in NATIVE_GATES:
		if gate._ideal_gate is None:
			continue
		# pyquil expects non-parametrized gates to be matrices and
		# parametrized ones to be functions that return matrices.
		if len(list(param for param in gate.parameter if param.classical)) == 0:
			dkt[gate.name.upper()] = gate.ideal_gate()
		else:
			dkt[gate.name.upper()] = gate.ideal_gate
	pyquil.gate_matrices.QUANTUM_GATES.update(dkt)
