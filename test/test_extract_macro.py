from unittest import TestCase

from .helpers.parser import ParserTesterMixin
from jaqal.extract_macro import extract_macro, MacroRecord
from jaqal.parse import make_lark_parser
from jaqal.identifier import Identifier


class ExtractMacroTester(ParserTesterMixin, TestCase):

    def test_extract_macro(self):
        text = "macro foo a { g a }"
        parser = make_lark_parser()
        exp_result = {Identifier.parse('foo'): MacroRecord(
            [Identifier.parse('a')],
            make_lark_parser(start='sequential_gate_block').parse('{ g a }')
        )}
        act_result = extract_macro(parser.parse(text))
        self.assertEqual(exp_result, act_result)

    def test_fail_on_redefined_macro(self):
        text = "macro foo { g }; macro foo { h}"
        with self.assertRaises(Exception):
            extract_macro(make_lark_parser().parse(text))