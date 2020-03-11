from unittest import TestCase

from jaqal.resolve_let import resolve_let, combine_let_dicts
from jaqal.identifier import Identifier
from jaqal.parse import make_lark_parser, TreeManipulators


class ResolveLetTester(TestCase):

    def test_replace_gate_arg(self):
        """Test replacing a single gate argument."""
        let_dict = {Identifier.parse('a'): 1}
        parser = make_lark_parser(start='gate_statement')
        text = "g a"
        exp_text = "g 1"
        exp_tree = parser.parse(exp_text)
        act_tree = resolve_let(parser.parse(text), let_dict)
        self.assertEqual(exp_tree, act_tree)

    def test_combine_dicts(self):
        main_dict = {Identifier.parse('foo'): 1, Identifier.parse('bar'): 2}
        addl_dict = {Identifier.parse('foo'): 42}
        comb_dict = combine_let_dicts(main_dict, addl_dict)
        self.assertEqual(comb_dict[Identifier.parse('foo')], 42)
        self.assertEqual(comb_dict[Identifier.parse('bar')], 2)

    def test_combine_dicts_extra_keys(self):
        """Test for failure when combining a dictionary that is not fully represented in the let values."""
        main_dict = {Identifier.parse('foo'): 1, Identifier.parse('bar'): 2}
        addl_dict = {Identifier.parse('foo'): 42, Identifier.parse('extra'): 666}
        with self.assertRaises(Exception):
            combine_let_dicts(main_dict, addl_dict)

    def test_replace_array_index(self):
        let_dict = {Identifier.parse('a'): 1}
        parser = make_lark_parser(start='gate_statement')
        text = "g arr[a]"
        exp_text = "g arr[1]"
        exp_tree = parser.parse(exp_text)
        act_tree = resolve_let(parser.parse(text), let_dict)
        self.assertEqual(exp_tree, act_tree)

    def test_reject_non_integer_array_index(self):
        let_dict = {Identifier.parse('a'): 3.14}
        parser = make_lark_parser(start='gate_statement')
        text = "g arr[a]"
        with self.assertRaises(Exception):
            resolve_let(parser.parse(text), let_dict)

    def test_replace_loop_count(self):
        let_dict = {Identifier.parse('a'): 1}
        parser = make_lark_parser(start='loop_statement')
        text = "loop a { g }"
        exp_text = "loop 1 { g }"
        exp_tree = parser.parse(exp_text)
        act_tree = resolve_let(parser.parse(text), let_dict)
        self.assertEqual(exp_tree, act_tree)

    def test_reject_negative_loop_count(self):
        let_dict = {Identifier.parse('a'): -1}
        parser = make_lark_parser(start='loop_statement')
        text = "loop a { g }"
        with self.assertRaises(Exception):
            resolve_let(parser.parse(text), let_dict)

    def test_reject_non_integer_loop_count(self):
        let_dict = {Identifier.parse('a'): 12.34}
        parser = make_lark_parser(start='loop_statement')
        text = "loop a { g }"
        with self.assertRaises(Exception):
            resolve_let(parser.parse(text), let_dict)

    def test_replace_register_statement(self):
        let_dict = {Identifier.parse('a'): 1}
        parser = make_lark_parser(start='register_statement')
        text = "register q[a]"
        exp_text = "register q[1]"
        exp_tree = parser.parse(exp_text)
        act_tree = resolve_let(parser.parse(text), let_dict)
        self.assertEqual(exp_tree, act_tree)

    def test_reject_negative_register_statement(self):
        let_dict = {Identifier.parse('a'): -1}
        parser = make_lark_parser(start='register_statement')
        text = "register q[a]"
        with self.assertRaises(Exception):
            resolve_let(parser.parse(text), let_dict)

    def test_reject_non_integer_register_statement(self):
        let_dict = {Identifier.parse('a'): 3.14}
        parser = make_lark_parser(start='register_statement')
        text = "register q[a]"
        with self.assertRaises(Exception):
            resolve_let(parser.parse(text), let_dict)

    def test_replace_map_statement(self):
        let_dict = {Identifier.parse('a'): 1, Identifier.parse('b'): 10, Identifier.parse('c'): 2}
        parser = make_lark_parser(start='map_statement')
        text = "map arr q[a:b:c]"
        exp_text = "map arr q[1:10:2]"
        exp_tree = parser.parse(exp_text)
        act_tree = resolve_let(parser.parse(text), let_dict)
        self.assertEqual(exp_tree, act_tree)

    def test_reject_non_integer_map_statement(self):
        let_dict = {Identifier.parse('a'): 3.14}
        parser = make_lark_parser(start='map_statement')
        text = "map arr q[0:a:2]"
        with self.assertRaises(Exception):
            resolve_let(parser.parse(text), let_dict)

    def test_dont_replace_macro_argument(self):
        let_dict = {Identifier.parse('a'): 3.14}
        parser = make_lark_parser(start='macro_definition')
        text = "macro foo a { g a }"
        exp_tree = parser.parse(text)
        act_tree = resolve_let(exp_tree, let_dict)
        self.assertEqual(exp_tree, act_tree)