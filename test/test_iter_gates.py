import unittest

from jaqal.iter_gates import parse_unitary_timed_gates
from jaqal.iter_gates import Gate, Loop, ParallelGateBlock, SequentialGateBlock


class GateParserTester(unittest.TestCase):

    def test_one_gate_no_arg(self):
        text = 'foo'
        exp_result = [
            Gate('foo', [])
        ]
        self.run_test(text, exp_result)

    def test_one_gate_with_args(self):
        text = 'reg r[6]; foo 1 3.14 r[5]'
        exp_result = [
            Gate('foo', [1, 3.14, ('r', 5)])
        ]
        self.run_test(text, exp_result)

    def test_gate_with_let(self):
        text = 'reg r[6]; let a 2; foo r[a]'
        exp_result = [
            Gate('foo', [('r', 2)])
        ]
        self.run_test(text, exp_result)

    def test_gate_with_map(self):
        text = 'reg r[6]; map q r; foo q[2]'
        exp_result = [
            Gate('foo', [('r', 2)])
        ]
        self.run_test(text, exp_result)

    def test_loop(self):
        text = 'loop 2 {foo; bar}'
        exp_result = [
            Loop(2, SequentialGateBlock([
                Gate('foo', []),
                Gate('bar', [])
            ]))
        ]
        self.run_test(text, exp_result)

    def test_macro_expansion(self):
        text = 'macro foo {g0; g1}; foo'
        exp_result = [
            Gate('g0', []),
            Gate('g1', [])
        ]
        self.run_test(text, exp_result)

    def test_parallel_block(self):
        text = '<foo|bar>'
        exp_result = [
            ParallelGateBlock([
                Gate('foo', []),
                Gate('bar', [])
            ])
        ]
        self.run_test(text, exp_result)

    def test_normalize_across_macro(self):
        text = 'macro foo <g0|{m0;m1}>; s0; <p0|{s1;foo}|{s2;s3;s4}>'
        exp_result = [
            Gate('s0', []),
            ParallelGateBlock([
                Gate('p0', []),
                Gate('s1', []),
                Gate('s2', [])
            ]),
            ParallelGateBlock([
                Gate('g0', []),
                Gate('m0', []),
                Gate('s3', [])
            ]),
            ParallelGateBlock([
                Gate('m1', []),
                Gate('s4', [])
            ])
        ]
        self.run_test(text, exp_result)

    def run_test(self, text, exp_result):
        act_result = self.make_gates(text)
        self.assertEqual(exp_result, act_result)

    def make_gates(self, text):
        gates = parse_unitary_timed_gates(text)
        return gates
