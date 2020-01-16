# The below IonUnroller class is a derivative work of Qiskit's Unroller class. It has been altered from the original.

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2018.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

from qiskit.transpiler.basepasses import TransformationPass
from qiskit.dagcircuit import DAGCircuit
from qiskit.exceptions import QiskitError
from qiskit.circuit import ParameterExpression
from qiskit.qasm import pi
from qiskit.extensions.standard.iden import IdGate
from qiskit.extensions.standard.x import XGate
from qiskit.extensions.standard.y import YGate
from qiskit.extensions.standard.rx import RXGate
from qiskit.extensions.standard.ry import RYGate
from qiskit.extensions.standard.rz import RZGate
from qiskit.circuit import QuantumRegister
from .gates import MSGate, SXGate, SYGate, RGate

class IonUnroller(TransformationPass):
	"""
	A Qiskit transpiler pass that attempts to map an arbitrary circuit onto the native
	gates of the QSCOUT hardware, usually to prepare for conversion to Jaqal.
	"""
	
	def __init__(self):
		super().__init__()
	
	def _get_rule(self, node):
		q = QuantumRegister(node.op.num_qubits, "q")
		if node.name == 'u1':
			rule = [(RZGate(node.op.params[0]), [q[0]], [])]
		elif node.name == 'u2':
			rule = [
				(RZGate(node.op.params[1]), [q[0]], []),
				(SYGate(), [q[0]], []),
				(RZGate(node.op.params[0]), [q[0]], []),
			]
		elif node.name == 'u3':
			rule = [
				(RZGate(node.op.params[2]), [q[0]], []),
				(RYGate(node.op.params[0]), [q[0]], []),
				(RZGate(node.op.params[1]), [q[0]], []),
			]
		elif node.name == 'cx':
			# // controlled-NOT as per Maslov (2017); this implementation takes s = v = +1
			# gate cx a,b
			# {
			# ry(pi/2) a;
			# ms(pi/2, pi/4) a,b;
			# rx(-pi/2) a;
			# rx(-pi/2) b;
			# ry(-pi/2) a;
			# }
			rule = [
				(SYGate(), [q[0]], []),
				(MSGate(pi/2, pi/4), [q[0], q[1]], []),
				(RXGate(-pi/2), [q[0]], []),
				(RXGate(-pi/2), [q[1]], []),
				(RYGate(-pi/2), [q[0]], []),
			]
		elif node.name == 'rx':
			if node.op.params[0] == pi:
				rule = [(XGate(), [q[0]], [])]
			elif node.op.params[0] == pi/2:
				rule = [(SXGate(), [q[0]], [])]
			else:
				rule = [(RGate(0, node.op.params[0]), [q[0]], [])]
		elif node.name == 'ry':
			if node.op.params[0] == pi:
				rule = [(YGate(), [q[0]], [])]
			elif node.op.params[0] == pi/2:
				rule = [(SYGate(), [q[0]], [])]
			else:
				rule = [(RGate(pi/2, node.op.params[0]), [q[0]], [])]
		else:
			rule = node.op.definition
		return rule
	
	def run(self, dag):
		"""
		Apply this transpiler pass to a circuit in directed acyclic graph representation.
		
		:param qiskit.dagcircuit.DAGCircuit dag: The circuit to transpile.
		:returns: The transpiled circuit.
		:rtype: qiskit.dagcircuit.DAGCircuit
		:raises qiskit.exceptions.QiskitError: If the circuit contains a parametrized non-basis gate, or contains a gate that cannot be unrolled.
		"""
		# Walk through the DAG and expand each non-basis node
		for node in dag.op_nodes():
			basic_insts = ['measure', 'reset', 'barrier', 'snapshot']
			if node.name in basic_insts:
				# TODO: this is legacy behavior.Basis_insts should be removed that these
				#  instructions should be part of the device-reported basis. Currently, no
				#  backend reports "measure", for example.
				continue
			if node.name in ['i', 'r', 'sx', 'sy', 'x', 'y', 'rz', 'ms2']:  # If already a base, ignore.
				continue

			try:
				rule = self._get_rule(node)
			except TypeError as err:
				if any(isinstance(p, ParameterExpression) for p in node.op.params):
					raise QiskitError('Unrolling gates parameterized by expressions '
									  'is currently unsupported.')
				raise QiskitError('Error decomposing node {}: {}'.format(node.name, err))

			if not rule:
				raise QiskitError("Cannot unroll the circuit to trapped ion gates. "
								  "No rule to expand instruction %s." %
								  node.op.name)

			# hacky way to build a dag on the same register as the rule is defined
			# TODO: need anonymous rules to address wires by index
			decomposition = DAGCircuit()
			qregs = {qb.register for inst in rule for qb in inst[1]}
			cregs = {cb.register for inst in rule for cb in inst[2]}
			for qreg in qregs:
				decomposition.add_qreg(qreg)
			for creg in cregs:
				decomposition.add_creg(creg)
			for inst in rule:
				decomposition.apply_operation_back(*inst)

			unrolled_dag = self.run(decomposition)	# recursively unroll ops
			dag.substitute_node_with_dag(node, unrolled_dag)
		return dag
