import unittest
from collections import defaultdict

import jaqalpaq.core as core
from jaqalpaq.core.algorithm import get_used_qubit_indices
from .. import common


class UsedQubitTester(unittest.TestCase):
    def test_single_gate_no_qubits(self):
        """Test a gate that does not use any qubits."""
        gate = common.make_random_gate_statement(count=0)
        exp_qubits = {}
        act_qubits = get_used_qubit_indices(gate)
        self.assertEqual(exp_qubits, act_qubits)

    def test_single_gate_one_qubit(self):
        """Test getting the single qubit used by a gate."""
        reg = common.make_random_register()
        qubit, index = common.choose_random_qubit_getitem(reg, return_params=True)
        gate_def, _, params = common.make_random_gate_definition(
            parameter_types=[core.ParamType.QUBIT], return_params=True
        )
        exp_qubits = {reg.name: {index}}
        args = {params[0].name: qubit}
        gate = core.GateStatement(gate_def, args)
        act_qubits = get_used_qubit_indices(gate)
        self.assertEqual(exp_qubits, act_qubits)

    def test_single_gate_mixed_args(self):
        """Test getting the qubits from a gate that mixes qubits and non-qubit arguments."""
        gate = common.make_random_gate_statement()
        exp_qubits = self.make_exp_qubits_from_gate(gate)
        act_qubits = get_used_qubit_indices(gate)
        self.assertEqual(exp_qubits, act_qubits)

    def test_loop(self):
        loop = common.make_random_loop_statement()
        exp_qubits = self.make_exp_qubits_from_block(loop.statements)
        act_qubits = get_used_qubit_indices(loop)
        self.assertEqual(exp_qubits, act_qubits)

    def test_block(self):
        block = common.make_random_block()
        exp_qubits = self.make_exp_qubits_from_block(block)
        act_qubits = get_used_qubit_indices(block)
        self.assertEqual(exp_qubits, act_qubits)

    def test_parallel_block(self):
        block = common.make_random_block(parallel=True)
        exp_qubits = self.make_exp_qubits_from_block(block)
        act_qubits = get_used_qubit_indices(block)
        self.assertEqual(exp_qubits, act_qubits)

    def test_circuit(self):
        # This doesn't fully exercise everything, like macros
        circuit = core.Circuit()
        block = common.make_random_block()
        circuit.body.statements.extend(block.statements)
        exp_qubits = self.make_exp_qubits_from_block(block)
        act_qubits = get_used_qubit_indices(circuit)
        self.assertEqual(exp_qubits, act_qubits)

    def test_macro(self):
        # I started making this a randomized test but things quickly got out of hand.

        # Define a macro that has a statement that uses a fixed qubit and another statement that uses
        # a qubit given as an argument.
        reg = core.Register("r", 3)
        param = core.Parameter("a", core.ParamType.QUBIT)
        gate_def = core.GateDefinition("g", [core.Parameter("p", core.ParamType.QUBIT)])
        g0 = gate_def(reg[0])
        g1 = gate_def(param)
        macro_body = core.BlockStatement(statements=(g0, g1))
        macro = core.Macro("foo", [param], macro_body)
        foo = macro(reg[2])
        exp_qubits = {"r": {0, 2}}
        act_qubits = get_used_qubit_indices(foo)
        self.assertEqual(exp_qubits, act_qubits)

    ##
    # Helper methods
    #

    def make_exp_qubits_from_block(self, block, context=None, exp_qubits=None):
        if exp_qubits is None:
            exp_qubits = defaultdict(set)
        for stmt in block.statements:
            assert isinstance(stmt, core.GateStatement)
            self.make_exp_qubits_from_gate(stmt, context=context, exp_qubits=exp_qubits)
        return exp_qubits

    def make_exp_qubits_from_gate(self, gate, context=None, exp_qubits=None):
        if exp_qubits is None:
            exp_qubits = defaultdict(set)
        for name, arg in gate.parameters.items():
            if isinstance(arg, core.NamedQubit):
                reg, index = arg.resolve_qubit()
                exp_qubits[reg.name].add(index)
            elif isinstance(arg, core.Register):
                # Not allowed in Jaqal but supported by jaqalpaq
                # We have to allow for both registers and map aliases here.
                for reg, idx in (
                    arg[i].resolve_qubit(context)
                    for i in range(arg.resolve_size(context))
                ):
                    exp_qubits[reg.name].add(idx)
        return exp_qubits
