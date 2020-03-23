from unittest import TestCase
from numbers import Number

from jaqalpup.core import (
    GateDefinition, Register, ScheduledCircuit, Parameter, BlockStatement, LoopStatement,
    NATIVE_GATES
)
from jaqalpup.jaqal.parser import parse_jaqal_string, Option


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

    def test_deduce_native_gates(self):
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

    def test_use_native_gates(self):
        """Test that we can use the native gates in the QSCOUT native gate set."""
        text = "register r[3]; Rx r[0] 1.5"
        exp_result = self.make_circuit(
            gates=[
                self.make_native_gate('Rx', ('r', 0), 1.5)
            ]
        )
        self.run_test(text, exp_result, use_qscout_native_gates=True)

    def test_fail_on_missing_native_gate(self):
        """Test that we fail when the using qscout native gates and the user uses a gate
        that does not exist."""
        text = "register r[3]; foo r[0] 1.5"
        # Make sure things we aren't doing something stupid and things will parse
        # without native gates on.
        parse_jaqal_string(text)
        with self.assertRaises(Exception):
            parse_jaqal_string(text, use_qscout_native_gates=True)

    ##
    # Helper methods
    #

    def run_test(self, text, exp_result=None, exp_registers=None, exp_native_gates=None,
                 override_dict=None, use_qscout_native_gates=False, option=Option.none):
        act_result = parse_jaqal_string(text, override_dict=override_dict,
                                        use_qscout_native_gates=use_qscout_native_gates,
                                        processing_option=option)
        if exp_result is not None:
            self.assertEqual(exp_result.body, act_result.body)
        if exp_registers is not None:
            self.assertEqual(exp_registers, act_result.registers)
        if exp_native_gates is not None:
            self.assertEqual(exp_native_gates, act_result.native_gates)

    @staticmethod
    def make_circuit(*, gates):
        circuit = ScheduledCircuit()
        for gate in gates:
            circuit.body.append(gate)
        return circuit

    def make_gate(self, name, *args):
        return self.make_gate_conditional(name, args, is_native=False)

    def make_native_gate(self, name, *args):
        return self.make_gate_conditional(name, args, is_native=True)

    def make_gate_conditional(self, name, args, is_native):
        arg_objects = [self.make_argument_object(arg) for arg in args]
        if is_native:
            gate_def = self.get_native_gate_definition(name)
        else:
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

    def get_native_gate_definition(self, name):
        for gate in NATIVE_GATES:
            if gate.name == name:
                return gate
        raise ValueError(f"Native gate {name} not found")

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
        return BlockStatement(parallel=True, statements=list(gates))

    def make_sequential_gate_block(self, *gates):
        return BlockStatement(parallel=False, statements=list(gates))

    def make_loop(self, *gates, count):
        return LoopStatement(count, self.make_sequential_gate_block(*gates))


class TestOption(TestCase):
    """Test the Option and OptionSet classes."""

    def test_contains_self(self):
        """Test that all options contain themselves."""
        for opt in Option:
            self.assertIn(opt, opt)

    def test_contains_bitmask(self):
        """Test that element containment acts like a bitmask."""
        for opt0 in Option:
            for opt1 in Option:
                self.assertEqual(opt0.value & opt1.value == opt1.value,
                                 opt1 in opt0)

    def test_in_option_set(self):
        """Test that options are in an option set containing them."""
        for opt0 in Option:
            for opt1 in Option:
                optset = opt0 | opt1
                self.assertIn(opt0, optset)
                self.assertIn(opt1, optset)

    def test_combine_opt_set_with_option(self):
        """Test that an option set combines with an option"""
        for opt0 in Option:
            for opt1 in Option:
                for opt2 in Option:
                    optset = opt0 | opt1
                    self.assertIn(opt2, optset | opt2)
                    self.assertIn(opt2, opt2 | optset)

    def test_let_in_optionset_with_let_map(self):
        """Test that extract_let is in an OptionSet that was created with extract_let_map but not extract_let"""
        optset = Option.expand_macro | Option.expand_let_map
        self.assertIn(Option.expand_let_map, optset)
