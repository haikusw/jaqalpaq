from unittest import TestCase

from jaqal.parse import make_lark_parser
from jaqal.extract_body import extract_body


class ExtractBodyTester(TestCase):

    def test_single_gate_statement(self):
        text = "g a 1 3.14"
        exp_statements = [
            ("g a 1 3.14", 'gate_statement')
        ]
        self.run_test(text, exp_statements)

    def test_loop_statement(self):
        text = "loop 1 { g }"
        exp_statements = [
            ("loop 1 { g }", 'loop_statement')
        ]
        self.run_test(text, exp_statements)

    def test_parallel_block(self):
        text = "< g | h >"
        exp_statements = [
            ("< g | h >", 'parallel_gate_block')
        ]
        self.run_test(text, exp_statements)

    def test_sequential_block(self):
        text = "{ g ; h }"
        exp_statements = [
            ("{ g ; h }", 'sequential_gate_block')
        ]
        self.run_test(text, exp_statements)

    def test_ignore_macro_definition(self):
        text = "macro foo { g }"
        exp_statements = []
        self.run_test(text, exp_statements)

    def run_test(self, text, exp_statements):
        parser = make_lark_parser()
        tree = parser.parse(text)
        act_result = extract_body(tree)
        exp_result = [make_lark_parser(start=start).parse(stmt) for stmt, start in exp_statements]
        self.assertEqual(act_result, exp_result)
