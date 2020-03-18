from unittest import TestCase
from numbers import Number

from qscout.core import (
    GateDefinition, Register, ScheduledCircuit, Parameter, GateBlock, LoopStatement
)
from qscout.jaqal.parser import parse_jaqal_string

class ParserTester(TestCase):

    def setUp(self):
        self.gate_definitions = {}
        self.registers = {}

    def test_gate_statement_no_args(self):
        text = "foo"
        exp_result = self.make_circuit(gates=[self.make_gate('foo')])
        self.run_test(text, exp_result)

    def test_gate_statement_numeric_arg(self):
        text = "foo 3.14"
        exp_result = self.make_circuit(gates=[self.make_gate('foo', 3.14)])
        self.run_test(text, exp_result)

    def test_gate_statement_qubit_arg(self):
        text = "register r[3]; foo r[1]"
        exp_result = self.make_circuit(
            gates=[
                self.make_gate('foo', ('r', 1))
            ]
        )
        self.run_test(text, exp_result)

    def test_let_override(self):
        text = "register r[3]; let a 1; let b 3.14; foo r[a] b"
        exp_result = self.make_circuit(
            gates=[
                self.make_gate('foo', ('r', 0), 1.41)
            ]
        )
        override_dict = {'a': 0, 'b': 1.41}
        self.run_test(text, exp_result, override_dict=override_dict)

    def test_parallel_block(self):
        text = "<foo | bar>"
        exp_result = self.make_circuit(
            gates=[
                self.make_parallel_gate_block(
                    self.make_gate('foo'),
                    self.make_gate('bar')
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_loop(self):
        text = "loop 32 { foo; bar }"
        exp_result = self.make_circuit(
            gates=[
                self.make_loop(
                    self.make_gate('foo'),
                    self.make_gate('bar'),
                    count=32
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_sequential_block_in_parallel_block(self):
        text = "< p | { foo; bar }>"
        exp_result = self.make_circuit(
            gates=[
                self.make_parallel_gate_block(
                    self.make_gate('p'),
                    self.make_sequential_gate_block(
                        self.make_gate('foo'),
                        self.make_gate('bar')
                    ),
                )
            ]
        )
        self.run_test(text, exp_result)

    def test_registers(self):
        """Test that the registers are properly read."""
        text = "register r[7]"
        exp_registers = {'r': Register('r', 7)}
        self.run_test(text, exp_registers=exp_registers)

    def test_native_gates(self):
        """Test that the native gates are properly deduced from the text."""
        # Note: This behavior is possibly not what we want long term
        text = "register r[3]; foo 1 r[0]; bar 3.14"
        exp_native_gates = {
            'foo': self.get_gate_definition(
                'foo',
                [self.make_parameter(0, 'float'), self.make_parameter(1, 'qubit')]
            ),
            'bar': self.get_gate_definition(
                'bar',
                [self.make_parameter(0, 'float')]
            )

        }
        self.run_test(text, exp_native_gates=exp_native_gates)

    ##
    # Helper methods
    #

    def run_test(self, text, exp_result=None, exp_registers=None, exp_native_gates=None,
                 override_dict=None):
        act_result = parse_jaqal_string(text, override_dict=override_dict)
        if exp_result is not None:
            self.assertEqual(exp_result.gates, act_result.gates)
        if exp_registers is not None:
            self.assertEqual(exp_registers, act_result.registers)
        if exp_native_gates is not None:
            self.assertEqual(exp_native_gates, act_result.native_gates)

    @staticmethod
    def make_circuit(*, gates):
        circuit = ScheduledCircuit()
        for gate in gates:
            circuit.gates.append(gate)
        return circuit

    def make_gate(self, name, *args):
        arg_objects = [self.make_argument_object(arg) for arg in args]
        params = [self.make_parameter_from_arg(idx, arg) for idx, arg in enumerate(args)]
        gate_def = self.get_gate_definition(name, params)
        return gate_def(*arg_objects)

    def get_gate_definition(self, name, params):
        if name not in self.gate_definitions:
            gate_def = GateDefinition(name, params)
            self.gate_definitions[name] = gate_def
        else:
            gate_def = self.gate_definitions[name]
        return gate_def

    def make_argument_object(self, arg):
        if isinstance(arg, Number):
            return arg
        elif isinstance(arg, tuple):
            return self.make_qubit(*arg)

    def make_qubit(self, name, index):
        if name not in self.registers:
            reg = Register(name, 1000)
            self.registers[name] = reg
            return reg[index]
        else:
            return self.registers[name][index]

    def make_parameter_from_arg(self, index, arg):
        kind = self.make_kind_from_arg(arg)
        param = self.make_parameter(index, kind)
        return param

    def make_kind_from_arg(self, arg):
        if isinstance(arg, Number):
            return 'float'
        elif isinstance(arg, tuple):
            return 'qubit'

    def make_parameter(self, index, kind):
        return Parameter(str(index), kind)

    def make_parallel_gate_block(self, *gates):
        return GateBlock(parallel=True, gates=list(gates))

    def make_sequential_gate_block(self, *gates):
        return GateBlock(parallel=False, gates=list(gates))

    def make_loop(self, *gates, count):
        return LoopStatement(count, self.make_sequential_gate_block(*gates))
