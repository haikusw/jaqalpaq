import unittest

from jaqalpaq import JaqalError
from jaqalpaq.core.algorithm.expand_macros import expand_macros
from jaqalpaq.parser import parse_jaqal_string
from jaqalpaq.core.circuitbuilder import build
import jaqalpaq.core as core


class ExpandMacrosTester(unittest.TestCase):
    def test_noop(self):
        """Test running macro resolution without resolving any macros."""
        text = "macro foo a b { g a b }; bar 1 2 3"
        exp_text = "bar 1 2 3"
        self.run_test(text, exp_text)

    def test_substitute_no_args(self):
        """Test substituting a macro with no arguments."""
        text = "macro foo { bar }; foo"
        exp_text = "bar"
        self.run_test(text, exp_text)

    def test_substitute_one_arg(self):
        """Test substituting a single macro argument."""
        text = "macro foo a { bar a }; foo 1"
        exp_text = "bar 1"
        self.run_test(text, exp_text)

    @unittest.expectedFailure
    def test_arguments_are_not_gates(self):
        """Test that when substituting gates are ignored, even if they have the same name as a parameter to a macro."""
        # TODO: This is not passing because of an issue in the
        # circuitbuilder
        text = "macro foo x { x }; foo 2"
        exp_text = "x"
        self.run_test(text, exp_text)

    @unittest.expectedFailure
    def test_define_macro_in_text(self):
        # TODO: Another problem with the circuitbuilder
        text = "foo; macro foo { bar }; foo"
        exp_text = "foo; { bar }"
        self.run_test(text, exp_text)

    def test_parallel_block(self):
        """Test resolving a macro with a parallel block."""
        text = "macro foo a < bar a | x >; foo 5"
        exp_text = "<bar 5 | x>"
        self.run_test(text, exp_text)

    def test_parallel_block_into_sequential_block(self):
        text = "macro foo a < bar a | x >; loop 5 {y ; foo 10}"
        exp_text = "loop 5 {y ; <bar 10 | x>}"
        self.run_test(text, exp_text)

    def test_sequential_into_sequential_block(self):
        """Test resolving a macro with a parallel block."""
        text = "macro foo a { bar a ; x }; loop 5 {y ; foo 1.123}"
        exp_text = "loop 5 {y ; bar 1.123 ; x}"
        self.run_test(text, exp_text)

    def test_parallel_into_parallel_block(self):
        """Test resolving a macro with a parallel block."""
        text = "macro foo a < bar a | x >; <y | foo 3>"
        exp_text = "<y | bar 3 | x >"
        self.run_test(text, exp_text)

    def test_reject_wrong_argument_count(self):
        macro = build(("macro", "foo", "a", ("sequential_block", ("gate", "bar", "a"))))
        gate = build(("gate", "foo", -1, -2))
        circuit = core.ScheduledCircuit()
        circuit.macros[macro.name] = macro
        circuit.body.statements.append(gate)
        with self.assertRaises(JaqalError):
            expand_macros(circuit)

    def run_test(self, text, exp_text):
        act_parsed = parse_jaqal_string(text)
        act_circuit = expand_macros(act_parsed)
        if isinstance(exp_text, str):
            exp_circuit = parse_jaqal_string(exp_text)
        else:
            exp_circuit = build(exp_text)
        if exp_circuit != act_circuit:
            print(f"Expected:\n{exp_circuit}")
            print(f"Actual:\n{act_circuit}")
        self.assertEqual(exp_circuit, act_circuit)


if __name__ == "__main__":
    unittest.main()
