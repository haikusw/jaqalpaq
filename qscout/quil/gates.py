from pyquil.gate_matrices import RX, RY
import numpy as np

def R(theta, phi):
	return np.array([[np.cos(phi / 2.0), (-1j * np.cos(theta) - np.sin(theta)) * np.sin(phi / 2.0)],
					[(-1j * np.cos(theta) + np.sin(theta)) * np.sin(phi / 2.0), np.cos(phi / 2.0)]])
SX = RX(np.pi/2)
SY = RY(np.pi/2)
def MS(theta, phi):
	return np.array([[np.cos(theta/2.0), 0, 0, -1j * (np.cos(phi * 2.0) - 1j * np.sin(phi * 2.0)) * np.sin(theta/2.0)],
					[0, np.cos(theta/2.0), -1j * np.sin(theta/2.0), 0],
					[0, -1j * np.sin(theta/2.0), np.cos(theta/2.0), 0],
					[-1j * (np.cos(phi * 2.0) - 1j * np.sin(phi * 2.0)) * np.sin(theta/2.0), 0, 0, np.cos(theta/2.0)]])
