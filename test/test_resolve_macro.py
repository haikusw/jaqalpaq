from unittest import TestCase

from jaqal.resolve_macro import resolve_macro
from .helpers.parser import ParserTesterMixin
from jaqal.parse import make_lark_parser
from jaqal.extract_macro import extract_macro


class ResolveMacroTester(ParserTesterMixin, TestCase):

    def test_noop(self):
        """Test running macro resolution without resolving any macros."""
        setup_text = "macro foo a b { g a b }"
        text = "bar x y z"
        exp_text = "bar x y z"
        self.run_test(setup_text, text, exp_text)

    def test_substitute_no_args(self):
        """Test substituting a macro with no arguments."""
        setup_text = "macro foo { bar }"
        text = "foo"
        exp_text = "bar"
        self.run_test(setup_text, text, exp_text)

    def test_substitute_one_arg(self):
        """Test substituting a single macro argument."""
        setup_text = "macro foo a { bar a }"
        text = "foo x"
        exp_text = "bar x"
        self.run_test(setup_text, text, exp_text)

    def test_arguments_are_not_gates(self):
        """Test that when substituting gates are ignored, even if they have the same name as a parameter to a macro."""
        setup_text = "macro foo x { x }"
        text = "foo a"
        exp_text = "x"
        self.run_test(setup_text, text, exp_text)

    def test_define_macro_in_text(self):
        setup_text = ""
        text = "foo; macro foo { bar }; foo"
        exp_text = "foo; macro foo { bar }; bar"
        self.run_test(setup_text, text, exp_text)

    def test_parallel_block(self):
        """Test resolving a macro with a parallel block."""
        setup_text = "macro foo a < bar a | x >"
        text = "foo p"
        exp_text = "<bar p | x>"
        self.run_test(setup_text, text, exp_text)

    def test_parallel_block_into_sequential_block(self):
        """Test resolving a macro with a parallel block."""
        setup_text = "macro foo a < bar a | x >"
        text = "loop 5 {y ; foo p}"
        exp_text = "loop 5 {y ; <bar p | x>}"
        self.run_test(setup_text, text, exp_text)

    def test_sequential_into_sequential_block(self):
        """Test resolving a macro with a parallel block."""
        setup_text = "macro foo a { bar a ; x }"
        text = "loop 5 {y ; foo p}"
        exp_text = "loop 5 {y ; bar p ; x}"
        self.run_test(setup_text, text, exp_text)

    def test_parallel_into_parallel_block(self):
        """Test resolving a macro with a parallel block."""
        setup_text = "macro foo a < bar a | x >"
        text = "<y | foo p>"
        exp_text = "<y | bar p | x >"
        self.run_test(setup_text, text, exp_text)

    def test_reject_wrong_argument_count(self):
        setup_text = "macro foo a { bar a }"
        text = "foo a b"
        self.run_reject_test(setup_text, text)

    def test_reject_redefine_macro(self):
        setup_text = "macro foo a { bar a }"
        text = "macro foo x { g x }"
        self.run_reject_test(setup_text, text)

    def run_test(self, setup_text, text, exp_text):
        parser = make_lark_parser()
        macro_dict = extract_macro(parser.parse(setup_text))
        tree = parser.parse(text)
        act_result = self.simplify_tree(resolve_macro(tree, macro_dict))
        exp_result = self.simplify_tree(parser.parse(exp_text))
        self.assertEqual(exp_result, act_result)

    def run_reject_test(self, setup_text, text):
        parser = make_lark_parser()
        with self.assertRaises(Exception):
            macro_dict = extract_macro(parser.parse(setup_text))
            tree = parser.parse(text)
            resolve_macro(tree, macro_dict)
