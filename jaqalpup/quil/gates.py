from pyquil.gate_matrices import RX, RY
import numpy as np

def R(theta, phi):
	"""
	Generates the unitary matrix that describes the QSCOUT native R gate, which performs
	an arbitrary rotation around an axis in the X-Y plane.
	
	:param float theta: The angle that sets the planar axis to rotate around.
	:param float phi: The angle by which the gate rotates the state.
	:returns: The unitary gate matrix.
	:rtype: numpy.array
	"""
	return np.array([[np.cos(phi / 2.0), (-1j * np.cos(theta) - np.sin(theta)) * np.sin(phi / 2.0)],
					[(-1j * np.cos(theta) + np.sin(theta)) * np.sin(phi / 2.0), np.cos(phi / 2.0)]])

SX = RX(np.pi/2)
SY = RY(np.pi/2)

def MS(theta, phi):
	"""
	Generates the unitary matrix that describes the QSCOUT native Mølmer-Sørensen gate.
	This matrix is equivalent to ::
	
		exp(-i theta/2 (cos(phi) XI + sin(phi) YI) (cos(phi) IX + sin(phi) IY))
		
	:param float theta: The angle by which the gate rotates the state.
	:param float phi: The phase angle determining the mix of XX and YY rotation.
	:returns: The unitary gate matrix.
	:rtype: numpy.array
	"""
	return np.array([[np.cos(theta/2.0), 0, 0, -1j * (np.cos(phi * 2.0) - 1j * np.sin(phi * 2.0)) * np.sin(theta/2.0)],
					[0, np.cos(theta/2.0), -1j * np.sin(theta/2.0), 0],
					[0, -1j * np.sin(theta/2.0), np.cos(theta/2.0), 0],
					[-1j * (np.cos(phi * 2.0) - 1j * np.sin(phi * 2.0)) * np.sin(theta/2.0), 0, 0, np.cos(theta/2.0)]])
