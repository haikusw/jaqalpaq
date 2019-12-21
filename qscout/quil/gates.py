from pyquil.gate_matrices import RX, RY
import numpy as np

def R(theta, phi):
	return np.array([[np.cos(phi / 2.0), (-1j * np.cos(theta) - np.sin(theta)) * np.sin(phi / 2.0)],
					[(-1j * np.cos(theta) + np.sin(theta)) * np.sin(phi / 2.0), np.cos(phi / 2.0)]])
SX = RX(np.pi/2)
SY = RY(np.pi/2)
def MS(theta, phi): # TODO phase correctly
	return np.array([[np.cos(theta), 0, 0, -1j * np.sin(theta)],
					[0, np.cos(theta), -1j * np.sin(theta), 0],
					[0, -1j * np.sin(theta), np.cos(theta), 0],
					[-1j * np.sin(theta), 0, 0, np.cos(theta)]])
