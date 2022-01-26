import unittest

from jaqalpaq.error import JaqalError
from jaqalpaq.core.algorithm.fill_in_let import fill_in_let
from jaqalpaq.parser import parse_jaqal_string
from jaqalpaq.core.circuitbuilder import build
import jaqalpaq.core as core


class FillInLetTester(unittest.TestCase):
    def test_noop(self):
        """Test not filling in any constants"""
        text = "let a 5; register q[3]; foo q[0]"
        exp_text = "let a 5; register q[3]; foo q[0]"
        self.run_test(text, exp_text)

    def test_gate_arg(self):
        """Test replacing a gate argument."""
        text = "let a 5; foo a"
        exp_text = "let a 5; foo 5"
        self.run_test(text, exp_text)

    def test_qubit_index(self):
        """Test replacing the index in a register as a gate argument."""
        text = "let a 0; register q[3]; foo q[a]"
        exp_text = "let a 0; register q[3]; foo q[0]"
        self.run_test(text, exp_text)

    def test_qubit_index_of_map(self):
        """Test replacing the index in a mapped register."""
        text = "let a 0; register q[3]; map r q; foo r[a]"
        exp_text = "let a 0; register q[3]; map r q; foo r[0]"
        self.run_test(text, exp_text)

    def test_qubit_index_of_slice(self):
        """Test replacing the index in a mapped slice."""
        text = "let a 0; register q[3]; map r q[a:]; foo r[1]"
        exp_text = "let a 0; register q[3]; map r q[0:]; foo r[1]"
        self.run_test(text, exp_text)

    def test_register_size(self):
        """Test replacing the size of a register."""
        text = "let sz 3; register q[sz]"
        exp_text = "let sz 3; register q[3]"
        self.run_test(text, exp_text)

    def test_map_index(self):
        """Test replacing the index of a single-qubit map."""
        text = "let a 2; register q[3]; map anc q[a]"
        exp_text = "let a 2; register q[3]; map anc q[2]"
        self.run_test(text, exp_text)

    def test_map_slice(self):
        """Test replacing the indexes of a map slice."""
        text = "let a 0; let b 3; let c 1; register q[5]; map r q[a:b:c]"
        exp_text = "let a 0; let b 3; let c 1; register q[5]; map r q[0:3:1]"
        self.run_test(text, exp_text)

    def test_sequential_block(self):
        """Test replacing something inside a parallel block."""
        text = "let a 2; { foo a; bar 8 }"
        exp_text = "let a 2; { foo 2; bar 8 }"
        self.run_test(text, exp_text)

    def test_parallel_block(self):
        """Test replacing something inside a parallel block."""
        text = "let a 2; < foo a | bar 8 >"
        exp_text = "let a 2; < foo 2 | bar 8 >"
        self.run_test(text, exp_text)

    def test_loop(self):
        """Test replacing something inside a loop body."""
        text = "let a 2; loop 5 { foo a }"
        exp_text = "let a 2; loop 5 { foo 2 }"
        self.run_test(text, exp_text)

    def test_loop_iteration(self):
        """Test replacing the loop iteration count."""
        text = "let cnt 7; loop cnt {}"
        exp_text = "let cnt 7; loop 7 {}"
        self.run_test(text, exp_text)

    def test_macro_body(self):
        """Test replacing a let within a macro body."""
        text = "let a 7; macro foo x { g x a }"
        exp_text = "let a 7; macro foo x { g x 7 }"
        self.run_test(text, exp_text)

    def test_macro_shadowed_by_parameter(self):
        """Test a macro with a parameter that is the same name as a let
        constant."""
        text = "let a 7; macro foo a { g a }"
        exp_text = "let a 7; macro foo a { g a }"
        self.run_test(text, exp_text)

    def test_gate_with_same_name(self):
        """Make sure no errors are raised when a gate has the same name as a
        let parameter, since they are in different namespaces."""
        text = "let foo 7; foo 1 2 3"
        exp_text = "let foo 7; foo 1 2 3"
        self.run_test(text, exp_text)

    def test_maintain_native_gates(self):
        """Make sure the native gates are properly passed through to the new
        circuit."""
        native_gates = {"foo": core.GateDefinition("foo")}
        text = "foo"
        exp_text = "foo"
        self.run_test(text, exp_text, inject_pulses=native_gates)

    def test_override_dict(self):
        """Test that the value in the override dict replaces the let value."""
        # Note: This would really have to check all possible
        # occurrences, but that's a lot of low payoff tests.
        text = "let a 7; foo a"
        exp_text = "let a 7; foo 5"
        override_dict = {"a": 5}
        self.run_test(text, exp_text, override_dict=override_dict)

    ##
    # Helper functions
    #

    def run_test(self, text, exp_text, inject_pulses=None, override_dict=None):
        act_parsed = parse_jaqal_string(
            text, inject_pulses=inject_pulses, autoload_pulses=False
        )
        act_circuit = fill_in_let(act_parsed, override_dict=override_dict)
        if isinstance(exp_text, str):
            exp_circuit = parse_jaqal_string(
                exp_text, inject_pulses=inject_pulses, autoload_pulses=False
            )
        else:
            exp_circuit = build(exp_text, inject_pulses=inject_pulses)
        if exp_circuit != act_circuit:
            print(f"Expected:\n{exp_circuit}")
            print(f"Actual:\n{act_circuit}")
        self.assertEqual(exp_circuit, act_circuit)
