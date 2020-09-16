from unittest import TestCase

from .helpers.parser import ParserTesterMixin
from jaqalpaq.parser.extract_usepulses import extract_usepulses
from jaqalpaq.parser.tree import make_lark_parser
from jaqalpaq.parser.identifier import Identifier


class ExtractLetTester(ParserTesterMixin, TestCase):
    def test_simple_usepulses_all(self):
        """Test importing all symbols from a namespace."""
        text = "from foo usepulses *"
        exp_value = {Identifier.parse("foo"): all}
        self.run_test(text, exp_value)

    def test_qualified_usepulses_all(self):
        """Test importing all symbols from a qualified namespace."""
        text = "from foo.bar usepulses *"
        exp_value = {Identifier.parse("foo.bar"): all}
        self.run_test(text, exp_value)

    def run_test(self, text, exp_value):
        parser = make_lark_parser()
        tree = parser.parse(text)
        act_value = extract_usepulses(tree)
        self.assertEqual(exp_value, act_value)
