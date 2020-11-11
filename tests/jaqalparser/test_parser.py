"""Test that the grammar properly parses Jaqal"""
import unittest

from jaqalpaq.parser.parser import parse_to_sexpression
from jaqalpaq.parser.identifier import Identifier


class ParserTester(unittest.TestCase):
    def test_comment(self):
        """Test parsing a single-line comment"""
        text = "//register q[3]\nregister q[2]"
        sexpr = ["circuit", ["register", "q", 2]]
        self.run_test(text, sexpr)

    def test_multiline_comment(self):
        """Test parsing a multi-line comment"""
        text = "/*register q[3]\nMore text\nlet a 2\n*/register q[2]"
        sexpr = ["circuit", ["register", "q", 2]]
        self.run_test(text, sexpr)

    def test_reg(self):
        """Test parsing the register statement"""
        text = "register q[3]"
        sexpr = ["circuit", ["register", "q", 3]]
        self.run_test(text, sexpr)

    def test_map_simple(self):
        """Test parsing the map statement with simple identifiers"""
        text = "map a b"
        sexpr = ["circuit", ["map", "a", "b"]]
        self.run_test(text, sexpr)

    def test_map_array(self):
        """Test parsing the map statement creating an array"""
        text = "map a q[1:3]"
        sexpr = ["circuit", ["map", "a", "q", 1, 3, None]]
        self.run_test(text, sexpr)

    def test_let_statement(self):
        """Test parsing the let statement"""
        text = "let pi 3.14"
        sexpr = ["circuit", ["let", "pi", 3.14]]
        self.run_test(text, sexpr)

    def test_let_with_semicolon(self):
        """Test parsing a let statement followed by a semicolon and newline."""
        text = "let pi 3.14;\nlet tau 6.28"
        sexpr = ["circuit", ["let", "pi", 3.14], ["let", "tau", 6.28]]
        self.run_test(text, sexpr)

    def test_usepulses_all(self):
        text = "from foo usepulses *"
        sexpr = ["circuit", ["usepulses", Identifier.parse("foo"), "*"]]
        self.run_test(text, sexpr)

    def test_gate_no_args(self):
        """Test a gate with no arguments."""
        text = "g"
        sexpr = ["circuit", ["gate", "g"]]
        self.run_test(text, sexpr)

    def test_gate_with_args(self):
        """Test a gate with arguments."""
        text = "g a 1 2.0 -3"
        sexpr = ["circuit", ["gate", "g", "a", 1, 2.0, -3]]
        self.run_test(text, sexpr)

    def test_gate_with_array_element(self):
        """Test a gate with an argument that is an element of an array."""
        text = "g q[0]"
        sexpr = ["circuit", ["gate", "g", ("array_item", "q", 0)]]
        self.run_test(text, sexpr)

    def test_gate_with_trailing_semicolon(self):
        text = "g;\nf"
        sexpr = ["circuit", ["gate", "g"], ["gate", "f"]]
        self.run_test(text, sexpr)

    def test_serial_gate_block(self):
        """Test a serial gate block with a separator."""
        text = "{g 0 ; h 1}"
        sexpr = ["circuit", ["sequential_block", ["gate", "g", 0], ["gate", "h", 1]]]
        self.run_test(text, sexpr)

    def test_serial_gate_block_nosep(self):
        """Test a serial gate block without a separator."""
        text = "{g 0 \n h 1}"
        sexpr = ["circuit", ["sequential_block", ["gate", "g", 0], ["gate", "h", 1]]]
        self.run_test(text, sexpr)

    def test_serial_gate_block_no_statements(self):
        text = "{}"
        sexpr = ["circuit", ["sequential_block"]]
        self.run_test(text, sexpr)

    def test_serial_gate_block_no_statements_with_newline(self):
        text = "{\n}"
        sexpr = ["circuit", ["sequential_block"]]
        self.run_test(text, sexpr)

    def test_serial_gate_block_separator_newline(self):
        text = "{g ;\n f}"
        sexpr = ["circuit", ["sequential_block", ["gate", "g"], ["gate", "f"]]]
        self.run_test(text, sexpr)

    def test_parallel_gate_block(self):
        """Test a parallel gate block with a separator."""
        text = "<g 0 | h 1>"
        sexpr = ["circuit", ["parallel_block", ["gate", "g", 0], ["gate", "h", 1]]]
        self.run_test(text, sexpr)

    def test_parallel_gate_block_nosep(self):
        """Test a parallel gate block with a separator."""
        text = "<g 0 \n h 1>"
        sexpr = ["circuit", ["parallel_block", ["gate", "g", 0], ["gate", "h", 1]]]
        self.run_test(text, sexpr)

    def test_parallel_gate_block_no_statements(self):
        text = "<>"
        sexpr = ["circuit", ["parallel_block"]]
        self.run_test(text, sexpr)

    def test_parallel_gate_block_no_statements_with_newline(self):
        text = "<\n>"
        sexpr = ["circuit", ["parallel_block"]]
        self.run_test(text, sexpr)

    def test_parallel_gate_block_separator_newline(self):
        text = "<g |\n f>"
        sexpr = ["circuit", ["parallel_block", ["gate", "g"], ["gate", "f"]]]
        self.run_test(text, sexpr)

    def test_macro_definition(self):
        """Test defining a macro."""
        text = "macro mymacro a b { g a ; h b }"
        sexpr = [
            "circuit",
            [
                "macro",
                "mymacro",
                "a",
                "b",
                ["sequential_block", ["gate", "g", "a"], ["gate", "h", "b"]],
            ],
        ]
        self.run_test(text, sexpr)

    def test_macro_definition_one_line(self):
        """Test defining a macro with no statements on one line."""
        text = "macro mymacro a { }"
        sexpr = ["circuit", ["macro", "mymacro", "a", ["sequential_block"]]]
        self.run_test(text, sexpr)

    def test_macro_definition_two_lines(self):
        """Test defining a macro with no statements on two lines."""
        text = "macro mymacro a {\n}"
        sexpr = ["circuit", ["macro", "mymacro", "a", ["sequential_block"]]]
        self.run_test(text, sexpr)

    def test_loop_statement(self):
        """Test creating a loop."""
        text = "loop 1 { g0 1 }"
        sexpr = ["circuit", ["loop", 1, ["sequential_block", ["gate", "g0", 1]]]]
        self.run_test(text, sexpr)

    def test_header(self):
        """Test a bunch of header statements together."""
        text = "register q[3]\nmap a q[0:3:2]\nlet pi 3.14; let reps 100\n"
        sexpr = [
            "circuit",
            ["register", "q", 3],
            ["map", "a", "q", 0, 3, 2],
            ["let", "pi", 3.14],
            ["let", "reps", 100],
        ]
        self.run_test(text, sexpr)

    def test_body(self):
        """Test a bunch of body statements together"""
        text = (
            "macro foo a b {\n"
            + "g0 a\n"
            + "g1 b\n"
            + "}\n"
            + "loop 5 < foo q r >\n"
            + "x q[7]\n"
        )
        sexpr = [
            "circuit",
            [
                "macro",
                "foo",
                "a",
                "b",
                ["sequential_block", ["gate", "g0", "a"], ["gate", "g1", "b"]],
            ],
            ["loop", 5, ["parallel_block", ["gate", "foo", "q", "r"]]],
            ["gate", "x", ("array_item", "q", 7)],
        ]
        self.run_test(text, sexpr)

    def test_nested_blocks(self):
        """Test nested parallel and sequential blocks."""
        text = "{<x a | y b> ; <{z 0 \n w 1}>}"
        sexpr = [
            "circuit",
            [
                "sequential_block",
                ["parallel_block", ["gate", "x", "a"], ["gate", "y", "b"]],
                [
                    "parallel_block",
                    ["sequential_block", ["gate", "z", 0], ["gate", "w", 1]],
                ],
            ],
        ]
        self.run_test(text, sexpr)

    def test_empty_line(self):
        """Test file beginning with empty lines"""
        text = "\nregister q[7]"
        sexpr = ["circuit", ["register", "q", 7]]
        self.run_test(text, sexpr)

    def test_comment_line(self):
        """Test full line comment"""
        text = "register q[7]\n// comment\n"
        sexpr = ["circuit", ["register", "q", 7]]
        self.run_test(text, sexpr)

    def test_line_with_whitespace(self):
        """Test line with whitespace"""
        text = "register q[7]\n \n"
        sexpr = ["circuit", ["register", "q", 7]]
        self.run_test(text, sexpr)

    def run_test(self, text, exp_sexpr):
        act_sexpr = parse_to_sexpression(text)
        self.assertEqual(exp_sexpr, act_sexpr)


if __name__ == "__main__":
    unittest.main()
