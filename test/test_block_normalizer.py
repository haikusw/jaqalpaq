import unittest

from jaqal.block_normalizer import normalize_blocks_with_unitary_timing
from jaqal.testing.mixin import ParserTesterMixin
from jaqal.parse import make_lark_parser


class BlockNormalizerTester(ParserTesterMixin, unittest.TestCase):

    def test_single_gate(self):
        text = 'foo 1 2 3'
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement('foo', 1, 2, 3)
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_sequential_block(self):
        """Test that a sequential block at top level is unwrapped."""
        text = '{foo}'
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement('foo')
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_parallel_block(self):
        """Test that a parallel block at top level remains unchanged."""
        text = '<foo|bar>'
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_parallel_gate_block(
                    self.make_gate_statement('foo'),
                    self.make_gate_statement('bar')
                )
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_top_level_loop(self):
        """Test that loops are allowed at the top level."""
        text = 'loop 5 {foo; bar}'
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_loop_statement(
                    5,
                    self.make_serial_gate_block(
                        self.make_gate_statement('foo'),
                        self.make_gate_statement('bar')
                    )
                )
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_seq_in_par_in_seq(self):
        """Test a sequential block in a parallel block in a sequential block."""
        text = '{g0;g1;<p0|p1|p2|{q0;q1}>;g2}'
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement('g0'),
                self.make_gate_statement('g1'),
                self.make_parallel_gate_block(
                    self.make_gate_statement('p0'),
                    self.make_gate_statement('p1'),
                    self.make_gate_statement('p2'),
                    self.make_gate_statement('q0')
                ),
                self.make_gate_statement('q1'),
                self.make_gate_statement('g2')
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_par_in_seq_in_par_1(self):
        """Test a parallel block in a sequential block in a parallel block."""
        text = '<p0|p1|{<g0|g1>;g2}>'
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_parallel_gate_block(
                    self.make_gate_statement('p0'),
                    self.make_gate_statement('p1'),
                    self.make_gate_statement('g0'),
                    self.make_gate_statement('g1')
                ),
                self.make_gate_statement('g2')
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_par_in_seq_in_par_2(self):
        """Test a parallel block in a sequential block in a parallel block."""
        text = '<p0|{<g0|g1>;g2}|{<a0|a1>;a2}|p1>'
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_parallel_gate_block(
                    self.make_gate_statement('p0'),
                    self.make_gate_statement('g0'),
                    self.make_gate_statement('g1'),
                    self.make_gate_statement('a0'),
                    self.make_gate_statement('a1'),
                    self.make_gate_statement('p1')
                ),
                self.make_parallel_gate_block(
                    self.make_gate_statement('g2'),
                    self.make_gate_statement('a2')
                )
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_reject_nested_loop(self):
        """Test that we reject a loop inside of a nested block."""
        text = '<{loop 5 {}}>'
        with self.assertRaises(Exception):
            self.make_simple_tree(text)

    def make_simple_tree(self, text):
        parser = make_lark_parser()
        tree = parser.parse(text)
        new_tree = self.simplify_tree(normalize_blocks_with_unitary_timing(tree))
        return new_tree
