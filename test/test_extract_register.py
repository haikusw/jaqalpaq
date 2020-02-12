from unittest import TestCase

from jaqal.testing.mixin import ParserTesterMixin
from jaqal.extract_register import extract_register
from jaqal.parse import make_lark_parser


class ExtractRegisterTester(ParserTesterMixin, TestCase):

    def test_single_register(self):
        text = "register q[3]"
        exp_result = {'q': 3}
        self.run_test(text, exp_result)

    def test_multiple_registers(self):
        text = "register q[3]; register r[2]"
        exp_result = {'q': 3, 'r': 2}
        self.run_test(text, exp_result)

    def test_duplicated_register(self):
        text = "register q[3]; register q[2]"
        parser = make_lark_parser()
        tree = parser.parse(text)
        with self.assertRaises(Exception):
            extract_register(tree)

    def run_test(self, text, exp_result):
        parser = make_lark_parser()
        tree = parser.parse(text)
        act_result = extract_register(tree)
        self.assertEqual(exp_result, act_result)
