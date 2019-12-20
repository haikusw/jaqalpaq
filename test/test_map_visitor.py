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
        # TODO: This case is actually ambiguous with the current grammar as q[1] can be an element or slice
        text = "reg q[3]; map a q[1]; foo a"
        exp_result = self.make_program(
            self.make_header_statements(self.make_register_statement(self.make_array_declaration('q', 3))),
            self.make_body_statements(self.make_gate_statement('foo', self.make_array_element('q', 1)))
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_macro_sub(self):
        """Test substitution within a macro."""
        text = "reg q[3]; map a q; macro foo {g0 a[0]}"
        exp_result = self.make_program(
            self.make_header_statements(self.make_register_statement(self.make_array_declaration('q', 3))),
            self.make_body_statements(
                self.make_macro_statement(
                    'foo',
                    self.make_serial_gate_block(
                        self.make_gate_statement('g0', self.make_array_element('q', 0))
                    )
                )
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_macro_nosub(self):
        """Test not substituting within a macro."""
        text = "reg q[3]; map b q[0]; macro foo {g0 a}"
        exp_result = self.make_program(
            self.make_header_statements(self.make_register_statement(self.make_array_declaration('q', 3))),
            self.make_body_statements(
                self.make_macro_statement(
                    'foo',
                    self.make_serial_gate_block(
                        self.make_gate_statement('g0', self.make_let_or_map_identifier('a'))
                    )
                )
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_macro_shadowed(self):
        """Test not substituting within a macro because the alias is shadowed by a parameter"""
        text = "reg q[3]; map b q[0]; macro foo b {g0 b}"
        exp_result = self.make_program(
            self.make_header_statements(self.make_register_statement(self.make_array_declaration('q', 3))),
            self.make_body_statements(
                self.make_macro_statement(
                    'foo',
                    'b',
                    self.make_serial_gate_block(
                        self.make_gate_statement('g0', self.make_let_or_map_identifier('b'))
                    )
                )
            )
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def make_simple_tree(self, text):
        parser = self.make_parser()
        tree = parser.parse(text)
        visited_tree = expand_map_values(tree)
        return self.simplify_tree(visited_tree)
