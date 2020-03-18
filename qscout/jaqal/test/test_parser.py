from unittest import TestCase
from numbers import Number

from qscout.core import GateDefinition, Register, ScheduledCircuit
from qscout.jaqal.parser import parse_jaqal_string

class ParserTester(TestCase):

    def setUp(self):
        self.gate_definitions = {}
        self.registers = {}

    def test_gate_statement_no_args(self):
        text = "foo"
        exp_result = self.make_circuit(gates=[self.make_gate('foo')])
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
        if name not in self.gate_definitions:
            params = [self.make_parameter(arg) for arg in args]
            gate_def = GateDefinition(name, params)
            self.gate_definitions[name] = gate_def
        else:
            gate_def = self.gate_definitions[name]
        return gate_def(*args)

    def make_parameter(self, arg):
        if isinstance(arg, Number):
            return 'float'
        elif isinstance(arg, tuple):
            return self.make_qubit(*arg)

    def make_qubit(self, name, index):
        if name not in self.registers:
            reg = Register(name, 1000)
            self.registers[name] = reg
            return reg[index]
        else:
            return self.registers[name][index]
