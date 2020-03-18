from unittest import TestCase
from numbers import Number

from qscout.core import GateDefinition, Register, ScheduledCircuit, Parameter
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

    ##
    # Helper methods
    #

    def run_test(self, text, exp_result, override_dict=None):
        act_result = parse_jaqal_string(text, override_dict=override_dict)
        self.assertEqual(exp_result.gates, act_result.gates)

    @staticmethod
    def make_circuit(*, gates):
        circuit = ScheduledCircuit()
        for gate in gates:
            circuit.gates.append(gate)
        return circuit

    def make_gate(self, name, *args):
        arg_objects = [self.make_argument_object(arg) for arg in args]
        if name not in self.gate_definitions:
            params = [self.make_parameter(idx, arg) for idx, arg in enumerate(args)]
            gate_def = GateDefinition(name, params)
            self.gate_definitions[name] = gate_def
        else:
            gate_def = self.gate_definitions[name]
        return gate_def(*arg_objects)

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

    def make_parameter(self, index, arg):
        if isinstance(arg, Number):
            return Parameter(str(index), 'float')
        elif isinstance(arg, tuple):
            return Parameter(str(index), 'qubit')
