import unittest

from jaqal.macro_context_visitor import MacroContextRewriteVisitor
from jaqal.parse import make_lark_parser


class TestVisitor(MacroContextRewriteVisitor):

    def __init__(self):
        super().__init__()
        self.context_by_gate = {}

    def visit_gate_statement(self, gate_name, gate_args):
        self.context_by_gate[self.extract_qualified_identifier(gate_name)] = self.macro_name


class MacroContextRewriteVisitorTester(unittest.TestCase):

    def test_track_macro(self):
        text = 'g0; macro m0 a b c {g1}'
        exp_result = {('g0',): None, ('g1',): 'm0'}
        parser = make_lark_parser()
        tree = parser.parse(text)
        visitor = TestVisitor()
        visitor.visit(tree)
        act_result = visitor.context_by_gate
        self.assertEqual(exp_result, act_result)
