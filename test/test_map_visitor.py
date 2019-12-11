from unittest import TestCase

from iqasm.testing.mixin import ParserTesterMixin
from iqasm.map_visitor import expand_map_values


class MapVisitorTester(ParserTesterMixin, TestCase):

    def test_full_replace(self):
        text = "reg q[3]; map a q; foo a[0]"
        exp_result = self.make_program(
            self.make_header_statements(self.make_register_statement(self.make_array_declaration('q', 3))),
            self.make_body_statements(self.make_gate_statement('foo', self.make_array_element('q', 0)))
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_replace_with_slice(self):
        """Test replacing an alias mapped onto a slice of a qubit register."""
        text = "reg q[7]; map a q[3:6:2]; foo a[1]"
        exp_result = self.make_program(
            self.make_header_statements(self.make_register_statement(self.make_array_declaration('q', 7))),
            self.make_body_statements(self.make_gate_statement('foo', self.make_array_element('q', 5)))
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_single_element(self):
        """Test a substitution of a single register location to a non-array alias."""
        text = "reg q[3]; map a q[1]; foo a"
        exp_result = self.make_program(
            self.make_header_statements(self.make_register_statement(self.make_array_declaration('q', 3))),
            self.make_body_statements(self.make_gate_statement('foo', 'a'))
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def make_simple_tree(self, text):
        parser = self.make_parser()
        tree = parser.parse(text)
        visited_tree = expand_map_values(tree)
        return self.simplify_tree(visited_tree)
