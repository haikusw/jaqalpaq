import unittest

from iqasm.testing.mixin import ParserTesterMixin
from iqasm.macro_expansion_visitor import expand_macros


class ExpandMacrosTester(ParserTesterMixin, unittest.TestCase):

    def test_expand_no_args(self):
        """Test expanding a macro in place with no arguments."""
        text = "macro foo {g0}; foo; g1"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement('g0'),
                self.make_gate_statement('g1')
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_expand_args(self):
        """Test expanding a macro in place with arguments."""
        text = "macro foo a b {g0 a; g1 b}; h; foo 1 2; g2"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement('h'),
                self.make_gate_statement('g0', 1),
                self.make_gate_statement('g1', 2),
                self.make_gate_statement('g2')
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def make_simple_tree(self, text):
        parser = self.make_parser()
        tree = parser.parse(text)
        visited_tree = expand_macros(tree)
        return self.simplify_tree(visited_tree)
