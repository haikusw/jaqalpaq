from pyquil.api import QAM

class QSCOUTAM(QAM):
	def load(self, executable):
		raise QSCOUTError("QSCOUT cannot run programs through the Quil API. Generate a QASM file with compile() and submit it directly to Peter Maunz.")
	def run(self):
		raise QSCOUTError("QSCOUT cannot run programs through the Quil API. Generate a QASM file with compile() and submit it directly to Peter Maunz.")
