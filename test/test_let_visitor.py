from unittest import TestCase

from iqasm.testing.mixin import ParserTesterMixin
from iqasm.let_visitor import expand_let_values


class LetVisitorTester(ParserTesterMixin, TestCase):

    def test_gate_argument(self):
        """Test replacing a gate argument."""
        text = "let x 5; foo x"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(self.make_gate_statement('foo', 5))
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_loop_count(self):
        """Test replacing the loop count."""
        text = "let x 5; loop x {}"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(self.make_loop_statement(5, self.make_serial_gate_block()))
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_array_declaration(self):
        """Test replacing the element count in an array declaration."""
        text = "let x 5; reg q[x]"
        exp_result = self.make_program(
            self.make_header_statements(
                self.make_register_statement(self.make_array_declaration('q', 5))
            ),
            self.make_body_statements()
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_array_element(self):
        """Test replacing the index in an array element."""
        text = "let x 5; foo q[x]"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(self.make_gate_statement('foo', self.make_array_element('q', 5)))
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_array_slice(self):
        """Test replacing elements of an array slice."""
        text = "let a 0; let b 10; let c 2; map r q[a:b:c]"
        exp_result = self.make_program(
            self.make_header_statements(
                self.make_map_statement('r', self.make_array_slice('q', 0, 10, 2))
            ),
            self.make_body_statements()
        )
        act_result = self.make_simple_tree(text)
        self.assertEqual(exp_result, act_result)

    def test_double_assign(self):
        """Test that two let statements defining the same value are rejected."""
        text = 'let a 0; let a 0'
        with self.assertRaises(Exception):
            self.make_simple_tree(text)

    def test_unknown_let(self):
        """Test that use of an unknown value raises an exception"""
        text = 'foo a[x]'
        with self.assertRaises(Exception):
            self.make_simple_tree(text)

    def test_unexpected_float(self):
        """Test using a floating point number where it does not belong."""
        text = 'let pi 3.14; reg qt[pi]'
        with self.assertRaises(Exception):
            self.make_simple_tree(text)

    def test_unexpected_negative(self):
        text = 'let a -3; foo arr[a]'
        with self.assertRaises(Exception):
            self.make_simple_tree(text)

    def test_override_dict(self):
        """Test using a dictionary to override the let statement given in the text."""
        text = 'let a 2; foo a'
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(self.make_gate_statement('foo', 5))
        )
        override_dict = {'a': 5}
        act_result = self.make_simple_tree(text, override_dict=override_dict)
        self.assertEqual(exp_result, act_result)

    def test_override_nonexistent_let(self):
        """Test that we cannot override a value that is not given in the text."""
        text = 'foo x[a]'
        override_dict = {'a': 5}
        with self.assertRaises(Exception):
            self.make_simple_tree(text, override_dict=override_dict)

    def make_simple_tree(self, text, override_dict=None):
        parser = self.make_parser()
        tree = parser.parse(text)
        visited_tree = expand_let_values(tree, override_dict=override_dict)
        return self.simplify_tree(visited_tree)
