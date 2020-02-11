from unittest import TestCase

from jaqal.testing.mixin import ParserTesterMixin
from jaqal.extract_let import extract_let
from jaqal.parse import make_lark_parser
from jaqal.identifier import Identifier

class ExtractLetTester(ParserTesterMixin, TestCase):

    def test_extract_integer(self):
        text = "let a 5"
        exp_value = {Identifier('a'): 5}
        self.run_test(text, exp_value)

    def test_extract_negative_integer(self):
        text = "let a -5"
        exp_value = {Identifier('a'): -5}
        self.run_test(text, exp_value)

    def test_extract_float(self):
        text = "let a 5.5"
        exp_value = {Identifier('a'): 5.5}
        self.run_test(text, exp_value)

    def test_extract_negative_float(self):
        text = "let a -5.5"
        exp_value = {Identifier('a'): -5.5}
        self.run_test(text, exp_value)

    def test_extract_duplicate(self):
        with self.assertRaises(Exception):
            text = "let a 5; let a 6"
            parser = make_lark_parser(start='let_statement')
            parser.parse(text)

    def run_test(self, text, exp_value):
        parser = make_lark_parser(start='let_statement')
        tree = parser.parse(text)
        act_value = extract_let(tree, use_float=True)
        self.assertEqual(exp_value, act_value)
