import unittest

from jaqalpaq.parser.macro_context_visitor import MacroContextRewriteVisitor
from jaqalpaq.parser.parse import make_lark_parser
from jaqalpaq.parser.identifier import Identifier


class MacroTaggerVisitor(MacroContextRewriteVisitor):
    def __init__(self):
        super().__init__()
        self.context_by_gate = {}

    def visit_gate_statement(self, gate_name, gate_args):
        self.context_by_gate[
            self.extract_qualified_identifier(gate_name)
        ] = self.macro_name


class MacroContextRewriteVisitorTester(unittest.TestCase):
    def test_track_macro(self):
        text = "g0; macro m0 a b c {g1}"
        exp_result = {
            Identifier.parse("g0"): None,
            Identifier.parse("g1"): Identifier.parse("m0"),
        }
        parser = make_lark_parser()
        tree = parser.parse(text)
        visitor = MacroTaggerVisitor()
        visitor.visit(tree)
        act_result = visitor.context_by_gate
        self.assertEqual(exp_result, act_result)
