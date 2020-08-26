"""Test that the grammar properly parses Jaqal"""
import unittest
import pathlib

# Accommodate both running from the test directory (as PyCharm does) and running from the project root.
from .helpers.parser import ParserTesterMixin
from jaqalpaq.parser.tree import make_lark_parser

top_grammar_filename = "jaqal/jaqal_grammar.lark"
test_grammar_filename = "../jaqal/jaqal_grammar.lark"

if pathlib.Path(top_grammar_filename).exists():
    grammar_filename = top_grammar_filename
elif pathlib.Path(test_grammar_filename):
    grammar_filename = test_grammar_filename
else:
    raise IOError("Cannot find grammar file")


class PreparseTester(ParserTesterMixin, unittest.TestCase):
    """Test pre-parsing steps, currently limited to qualified identifier expansion."""

    def test_gate_with_qualified_identifier(self):
        text = "foo.g"
        parser = make_lark_parser(start="gate_statement")
        tree = parser.parse(text)
        exp_tree = self.make_gate_statement("foo.g")
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_qualified_gate_arg(self):
        text = "g foo.a bar.b"
        parser = make_lark_parser(start="gate_statement")
        tree = parser.parse(text)
        exp_tree = self.make_gate_statement(
            "g",
            self.make_let_or_map_identifier("foo.a"),
            self.make_let_or_map_identifier("bar.b"),
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_qualified_loop_count(self):
        text = "loop foo.a { g }"
        parser = make_lark_parser(start="loop_statement")
        tree = parser.parse(text)
        exp_tree = self.make_loop_statement(
            "foo.a", self.make_serial_gate_block(self.make_gate_statement("g"))
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_disallow_in_let(self):
        text = "let foo.a 42"
        parser = make_lark_parser(start="let_statement")
        with self.assertRaises(Exception):
            parser.parse(text)

    def test_disallow_in_macro_arg(self):
        text = "macro foo.a { g }"
        parser = make_lark_parser(start="macro_definition")
        with self.assertRaises(Exception):
            parser.parse(text)

    def test_disallow_in_register(self):
        text = "register foo.a[5]"
        parser = make_lark_parser(start="register_statement")
        with self.assertRaises(Exception):
            parser.parse(text)


class ParserTester(ParserTesterMixin, unittest.TestCase):
    def test_comment(self):
        """Test parsing a single-line comment"""
        text = "//register q[3]\nregister q[2]"
        parser = make_lark_parser(start="start")
        tree = parser.parse(text)
        exp_tree = self.make_program(
            self.make_header_statements(
                self.make_register_statement(self.make_array_declaration("q", 2))
            ),
            self.make_body_statements(),
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_multiline_comment(self):
        """Test parsing a single-line comment"""
        text = "/*register q[3]\nMore text\nlet a 2\n*/register q[2]"
        parser = make_lark_parser(start="start")
        tree = parser.parse(text)
        exp_tree = self.make_program(
            self.make_header_statements(
                self.make_register_statement(self.make_array_declaration("q", 2))
            ),
            self.make_body_statements(),
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_reg(self):
        """Test parsing the register statement"""
        text = "register q[3]"
        parser = make_lark_parser(start="register_statement")
        tree = parser.parse(text)
        exp_tree = self.make_register_statement(self.make_array_declaration("q", 3))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_map_simple(self):
        """Test parsing the map statement with simple identifiers"""
        text = "map a b"
        parser = make_lark_parser(start="map_statement")
        tree = parser.parse(text)
        exp_tree = self.make_map_statement("a", self.make_identifier("b"))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_map_array(self):
        """Test parsing the map statement creating an array"""
        text = "map a q[1:3]"
        parser = make_lark_parser(start="map_statement")
        tree = parser.parse(text)
        exp_tree = self.make_map_statement("a", self.make_array_slice("q", 1, 3, None))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_let_statement(self):
        """Test parsing the let statement"""
        text = "let pi 3.14"
        parser = make_lark_parser(start="let_statement")
        tree = parser.parse(text)
        exp_tree = self.make_let_statement("pi", 3.14)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_let_with_semicolon(self):
        """Test parsing a let statement followed by a semicolon and newline."""
        text = "let pi 3.14;\nlet tau 6.28"
        parser = make_lark_parser(start="start")
        tree = parser.parse(text)
        exp_tree = self.make_program(
            self.make_header_statements(
                self.make_let_statement("pi", 3.14),
                self.make_let_statement("tau", 6.28),
            ),
            self.make_body_statements(),
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_statement(self):
        """Test parsing an import statement."""
        text = "import foo"
        parser = make_lark_parser(start="import_statement")
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(None, [self.make_as_clause("foo")])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_as_statement(self):
        text = "import foo as bar"
        parser = make_lark_parser(start="import_statement")
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(None, [self.make_as_clause("foo", "bar")])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_from_statement(self):
        text = "from foo import bar"
        parser = make_lark_parser(start="import_statement")
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(
            self.make_from_clause("foo"), [self.make_as_clause("bar")]
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_from_as_statement(self):
        text = "from foo import bar0 as bar1"
        parser = make_lark_parser(start="import_statement")
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(
            self.make_from_clause("foo"), [self.make_as_clause("bar0", "bar1")]
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_all(self):
        text = "from foo import *"
        parser = make_lark_parser(start="import_statement")
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(
            self.make_from_clause("foo"), [self.make_all_module()]
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_usepulses_statement(self):
        """Test parsing an usepulses statement."""
        text = "usepulses foo"
        parser = make_lark_parser(start="usepulses_statement")
        tree = parser.parse(text)
        exp_tree = self.make_usepulses_statement(None, [self.make_as_clause("foo")])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_usepulses_as_statement(self):
        text = "usepulses foo as bar"
        parser = make_lark_parser(start="usepulses_statement")
        tree = parser.parse(text)
        exp_tree = self.make_usepulses_statement(
            None, [self.make_as_clause("foo", "bar")]
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_usepulses_from_statement(self):
        text = "from foo usepulses bar"
        parser = make_lark_parser(start="usepulses_statement")
        tree = parser.parse(text)
        exp_tree = self.make_usepulses_statement(
            self.make_from_clause("foo"), [self.make_as_clause("bar")]
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_usepulses_from_as_statement(self):
        text = "from foo usepulses bar0 as bar1"
        parser = make_lark_parser(start="usepulses_statement")
        tree = parser.parse(text)
        exp_tree = self.make_usepulses_statement(
            self.make_from_clause("foo"), [self.make_as_clause("bar0", "bar1")]
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_usepulses_all(self):
        text = "from foo usepulses *"
        parser = make_lark_parser(start="usepulses_statement")
        tree = parser.parse(text)
        exp_tree = self.make_usepulses_statement(
            self.make_from_clause("foo"), [self.make_all_module()]
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_gate_no_args(self):
        """Test a gate with no arguments."""
        text = "g"
        parser = make_lark_parser(start="gate_statement")
        tree = parser.parse(text)
        exp_tree = self.make_gate_statement("g")
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_gate_with_args(self):
        """Test a gate with arguments."""
        text = "g a 1 2.0 -3"
        parser = make_lark_parser(start="gate_statement")
        tree = parser.parse(text)
        exp_tree = self.make_gate_statement("g", "a", 1, 2.0, -3)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_gate_with_array_element(self):
        """Test a gate with an argument that is an element of an array."""
        text = "g q[0]"
        parser = make_lark_parser(start="gate_statement")
        tree = parser.parse(text)
        exp_tree = self.make_gate_statement("g", self.make_array_element_qual("q", 0))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_gate_with_trailing_semicolon(self):
        text = "g;\nf"
        parser = make_lark_parser(start="start")
        tree = parser.parse(text)
        exp_tree = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement("g"), self.make_gate_statement("f")
            ),
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_serial_gate_block(self):
        """Test a serial gate block with a separator."""
        text = "{g 0 ; h 1}"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_serial_gate_block(
            self.make_gate_statement("g", 0), self.make_gate_statement("h", 1)
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_serial_gate_block_nosep(self):
        """Test a serial gate block without a separator."""
        text = "{g 0 \n h 1}"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_serial_gate_block(
            self.make_gate_statement("g", 0), self.make_gate_statement("h", 1)
        )
        act_tree = self.simplify_tree(tree)

        self.assertEqual(exp_tree, act_tree)

    def test_serial_gate_block_no_statements(self):
        text = "{}"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_serial_gate_block()
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_serial_gate_block_no_statements_with_newline(self):
        text = "{\n}"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_serial_gate_block()
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_serial_gate_block_separator_newline(self):
        text = "{g ;\n f}"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_serial_gate_block(
            self.make_gate_statement("g"), self.make_gate_statement("f")
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_parallel_gate_block(self):
        """Test a parallel gate block with a separator."""
        text = "<g 0 | h 1>"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_parallel_gate_block(
            self.make_gate_statement("g", 0), self.make_gate_statement("h", 1)
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_parallel_gate_block_nosep(self):
        """Test a parallel gate block with a separator."""
        text = "<g 0 \n h 1>"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_parallel_gate_block(
            self.make_gate_statement("g", 0), self.make_gate_statement("h", 1)
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_parallel_gate_block_no_statements(self):
        text = "<>"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_parallel_gate_block()
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_parallel_gate_block_no_statements_with_newline(self):
        text = "<\n>"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_parallel_gate_block()
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_parallel_gate_block_separator_newline(self):
        text = "<g |\n f>"
        parser = make_lark_parser(start="gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_parallel_gate_block(
            self.make_gate_statement("g"), self.make_gate_statement("f")
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_macro_definition(self):
        """Test defining a macro."""
        text = "macro mymacro a b { g a ; h b }"
        parser = make_lark_parser(start="macro_definition")
        tree = parser.parse(text)
        gate_block = self.make_serial_gate_block(
            self.make_gate_statement("g", "a"), self.make_gate_statement("h", "b")
        )
        exp_tree = self.make_macro_statement("mymacro", "a", "b", gate_block)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_macro_definition_one_line(self):
        """Test defining a macro with no statements on one line."""
        text = "macro mymacro a { }"
        parser = make_lark_parser(start="macro_definition")
        tree = parser.parse(text)
        gate_block = self.make_serial_gate_block()
        exp_tree = self.make_macro_statement("mymacro", "a", gate_block)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_macro_definition_two_lines(self):
        """Test defining a macro with no statements on two lines."""
        text = "macro mymacro a {\n}"
        parser = make_lark_parser(start="macro_definition")
        tree = parser.parse(text)
        gate_block = self.make_serial_gate_block()
        exp_tree = self.make_macro_statement("mymacro", "a", gate_block)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_loop_statement(self):
        """Test creating a loop."""
        text = "loop 1 { g0 1 }"
        parser = make_lark_parser(start="loop_statement")
        tree = parser.parse(text)
        exp_tree = self.make_loop_statement(
            1, self.make_serial_gate_block(self.make_gate_statement("g0", 1))
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_header(self):
        """Test a bunch of header statements together."""
        text = "register q[3]\n" + "map a q[0:3:2]\n" + "let pi 3.14; let reps 100\n"
        parser = make_lark_parser(start="header_statements")
        tree = parser.parse(text)
        reg_stmt = self.make_register_statement(self.make_array_declaration("q", 3))
        map_stmt = self.make_map_statement("a", self.make_array_slice("q", 0, 3, 2))
        let0_stmt = self.make_let_statement("pi", 3.14)
        let1_stmt = self.make_let_statement("reps", 100)
        exp_tree = self.make_header_statements(reg_stmt, map_stmt, let0_stmt, let1_stmt)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

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
        parser = make_lark_parser(start="body_statements")
        tree = parser.parse(text)
        macro_body = self.make_serial_gate_block(
            self.make_gate_statement("g0", "a"), self.make_gate_statement("g1", "b")
        )
        macro_def = self.make_macro_statement("foo", "a", "b", macro_body)
        loop_block = self.make_parallel_gate_block(
            self.make_gate_statement("foo", "q", "r")
        )
        loop_stmt = self.make_loop_statement(5, loop_block)
        gate_stmt = self.make_gate_statement("x", self.make_array_element_qual("q", 7))
        exp_tree = self.make_body_statements(macro_def, loop_stmt, gate_stmt)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_nested_blocks(self):
        """Test nested parallel and sequential blocks."""
        text = "{<x a | y b> ; <{z 0 \n w 1}>}"
        parser = make_lark_parser(start="sequential_gate_block")
        tree = parser.parse(text)
        exp_tree = self.make_serial_gate_block(
            self.make_parallel_gate_block(
                self.make_gate_statement("x", "a"), self.make_gate_statement("y", "b")
            ),
            self.make_parallel_gate_block(
                self.make_serial_gate_block(
                    self.make_gate_statement("z", 0), self.make_gate_statement("w", 1)
                )
            ),
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_empty_line(self):
        """Test file beginning with empty lines"""
        text = "\nregister q[7]"
        parser = make_lark_parser()
        parser.parse(text)

    def test_comment_line(self):
        """Test full line comment"""
        text = "register q[7]\n// comment\n"
        parser = make_lark_parser()
        parser.parse(text)

    def test_line_with_whitespace(self):
        """Test line with whitespace"""
        text = "register q[7]\n \n"
        parser = make_lark_parser()
        parser.parse(text)


if __name__ == "__main__":
    unittest.main()
