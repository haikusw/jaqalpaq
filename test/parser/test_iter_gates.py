import unittest

from jaqal.parser.iter_gates import get_gates_and_loops
from jaqal.parser.iter_gates import Gate, Loop, ParallelGateBlock, SequentialGateBlock
from jaqal.parser.parse import parse_with_lark


class GateParserTester(unittest.TestCase):

    def test_one_gate_no_arg(self):
        text = 'foo'
        exp_result = [
            Gate('foo', [])
        ]
        self.run_test(text, exp_result)

    def test_one_gate_with_args(self):
        text = 'register r[6]; foo 1 3.14 r[5]'
        exp_result = [
            Gate('foo', [1, 3.14, ('r', 5)])
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

    def test_parallel_block(self):
        text = '<foo|bar>'
        exp_result = [
            ParallelGateBlock([
                Gate('foo', []),
                Gate('bar', [])
            ])
        ]
        self.run_test(text, exp_result)

    def run_test(self, text, exp_result):
        act_result = self.make_gates(text)
        self.assertEqual(exp_result, act_result)

    def make_gates(self, text):
        tree = parse_with_lark(text)
        gates = get_gates_and_loops(tree)
        return gates
