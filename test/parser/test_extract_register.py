from unittest import TestCase

from .helpers.parser import ParserTesterMixin
from jaqal.parser.extract_register import extract_register
from jaqal.parser.parse import make_lark_parser, TreeManipulators
from jaqal.parser.identifier import Identifier


class ExtractRegisterTester(ParserTesterMixin, TestCase):

    def test_single_register(self):
        text = "register q[3]"
        exp_result = {
            Identifier.parse('q'): TreeManipulators.make_let_or_integer(
                TreeManipulators.make_integer(3)
            )
        }
        self.run_test(text, exp_result)

    def test_multiple_registers(self):
        text = "register q[3]; register r[2]"
        exp_result = {Identifier.parse('q'): TreeManipulators.make_let_or_integer(TreeManipulators.make_integer(3)),
                      Identifier.parse('r'): TreeManipulators.make_let_or_integer(TreeManipulators.make_integer(2))}
        self.run_test(text, exp_result)

    def test_duplicated_register(self):
        text = "register q[3]; register q[2]"
        parser = make_lark_parser()
        tree = parser.parse(text)
        with self.assertRaises(Exception):
            extract_register(tree)

    def test_let_constant_as_size(self):
        text = "let a 5; register q[a]"
        exp_result = {
            Identifier.parse('q'): TreeManipulators.make_let_or_integer(
                TreeManipulators.make_let_identifier(
                    TreeManipulators.make_qualified_identifier('a')
                )
            )
        }
        self.run_test(text, exp_result)

    def run_test(self, text, exp_result):
        parser = make_lark_parser()
        tree = parser.parse(text)
        act_result = extract_register(tree)
        self.assertEqual(exp_result, act_result)
