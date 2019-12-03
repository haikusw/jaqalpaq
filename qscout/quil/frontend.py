from qscout.core import ScheduledCircuit
from qscout import QSCOUTError
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
	device = get_ion_device(num_qubits)
	return QuantumComputer(name="QSCOUT-%d" % num_qubits, qam=get_ion_qam(), device=device, compiler=IonCompiler(device))

def patch_simulator():
	from .gates import R, SX, SY, MS
	pyquil.gate_matrices.QUANTUM_GATES.update({'R': R, 'SX': SX, 'SY': SY, 'MS': MS})