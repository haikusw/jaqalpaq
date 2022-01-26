import unittest

from jaqalpaq.error import JaqalError
from jaqalpaq.parser import parse_jaqal_string
from jaqalpaq.core.algorithm.unit_timing import normalize_blocks_with_unitary_timing


class UnitTimingTester(unittest.TestCase):
    def test_single_gate(self):
        test = "foo 1 2 3"
        exp = "foo 1 2 3"
        self.run_test(test, exp)

    def test_sequential_block(self):
        test = "{foo}"
        exp = "foo"
        self.run_test(test, exp)

    def test_parallel_block(self):
        test = "<foo|bar>"
        exp = "<foo|bar>"
        self.run_test(test, exp)

    def test_top_level_loop(self):
        test = "loop 5 {foo; bar}"
        exp = "loop 5 {foo; bar}"
        self.run_test(test, exp)

    def test_seq_in_par_in_seq(self):
        test = "{g0;g1;<p0|p1|p2|{q0;q1}>;g2}"
        exp = "g0;g1;<p0|p1|p2|q0>;q1;g2"
        self.run_test(test, exp)

    def test_par_in_seq_in_par_1(self):
        test = "<p0|p1|{<g0|g1>;g2}>"
        exp = "<p0|p1|g0|g1>;g2"
        self.run_test(test, exp)

    def test_par_in_seq_in_par_2(self):
        test = "<p0|{<g0|g1>;g2}|{<a0|a1>;a2}|p1>"
        exp = "<p0|g0|g1|a0|a1|p1>;<g2|a2>"
        self.run_test(test, exp)

    def test_reject_nested_loop(self):
        test = "<{loop 5 {}}>"
        with self.assertRaises(JaqalError):
            normalize_blocks_with_unitary_timing(
                parse_jaqal_string(test, autoload_pulses=False)
            )

    def run_test(self, test, exp):
        exp_result = parse_jaqal_string(exp, autoload_pulses=False)
        test_parsed = parse_jaqal_string(test, autoload_pulses=False)
        act_result = normalize_blocks_with_unitary_timing(test_parsed)
        self.assertEqual(exp_result, act_result)


if __name__ == "__main__":
    unittest.main()
