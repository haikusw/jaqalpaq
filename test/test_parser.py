"""Test that the grammar properly parses Jaqal"""
import unittest
import pathlib

# Accommodate both running from the test directory (as PyCharm does) and running from the project root.
from jaqal.testing.mixin import ParserTesterMixin

top_grammar_filename = 'jaqal/jaqal_grammar.lark'
test_grammar_filename = '../jaqal/jaqal_grammar.lark'

if pathlib.Path(top_grammar_filename).exists():
    grammar_filename = top_grammar_filename
elif pathlib.Path(test_grammar_filename):
    grammar_filename = test_grammar_filename
else:
    raise IOError('Cannot find grammar file')


class ParserTester(ParserTesterMixin, unittest.TestCase):

    def test_reg(self):
        """Test parsing the register statement"""
        text = "reg q[3]"
        parser = self.make_parser(start='register_statement')
        tree = parser.parse(text)
        exp_tree = self.make_register_statement(self.make_array_declaration('q', 3))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_map_simple(self):
        """Test parsing the map statement with simple identifiers"""
        text = "map a b"
        parser = self.make_parser(start='map_statement')
        tree = parser.parse(text)
        exp_tree = self.make_map_statement('a', self.make_identifier('b'))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_map_array(self):
        """Test parsing the map statement creating an array"""
        text = "map a q[1:3]"
        parser = self.make_parser(start='map_statement')
        tree = parser.parse(text)
        exp_tree = self.make_map_statement('a', self.make_array_slice('q', 1, 3, None))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_let_statement(self):
        """Test parsing the let statement"""
        text = "let pi 3.14"
        parser = self.make_parser(start='let_statement')
        tree = parser.parse(text)
        exp_tree = self.make_let_statement('pi', 3.14)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_statement(self):
        """Test parsing an import statement."""
        text = "import foo"
        parser = self.make_parser(start='import_statement')
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(None, [self.make_as_clause('foo')])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_as_statement(self):
        text = "import foo as bar"
        parser = self.make_parser(start='import_statement')
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(None, [self.make_as_clause('foo', 'bar')])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_from_statement(self):
        text = "from foo import bar"
        parser = self.make_parser(start='import_statement')
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(self.make_from_clause('foo'), [self.make_as_clause('bar')])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_from_as_statement(self):
        text = "from foo import bar0 as bar1"
        parser = self.make_parser(start='import_statement')
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(self.make_from_clause('foo'), [self.make_as_clause('bar0', 'bar1')])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_import_all(self):
        text = "from foo import *"
        parser = self.make_parser(start='import_statement')
        tree = parser.parse(text)
        exp_tree = self.make_import_statement(self.make_from_clause('foo'), [self.make_all_module()])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_require_statement(self):
        """Test parsing an require statement."""
        text = "require foo"
        parser = self.make_parser(start='require_statement')
        tree = parser.parse(text)
        exp_tree = self.make_require_statement(None, [self.make_as_clause('foo')])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_require_as_statement(self):
        text = "require foo as bar"
        parser = self.make_parser(start='require_statement')
        tree = parser.parse(text)
        exp_tree = self.make_require_statement(None, [self.make_as_clause('foo', 'bar')])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_require_from_statement(self):
        text = "from foo require bar"
        parser = self.make_parser(start='require_statement')
        tree = parser.parse(text)
        exp_tree = self.make_require_statement(self.make_from_clause('foo'), [self.make_as_clause('bar')])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_require_from_as_statement(self):
        text = "from foo require bar0 as bar1"
        parser = self.make_parser(start='require_statement')
        tree = parser.parse(text)
        exp_tree = self.make_require_statement(self.make_from_clause('foo'), [self.make_as_clause('bar0', 'bar1')])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_require_all(self):
        text = "from foo require *"
        parser = self.make_parser(start='require_statement')
        tree = parser.parse(text)
        exp_tree = self.make_require_statement(self.make_from_clause('foo'), [self.make_all_module()])
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_gate_no_args(self):
        """Test a gate with no arguments."""
        text = "g"
        parser = self.make_parser(start='gate_statement')
        tree = parser.parse(text)
        exp_tree = self.make_gate_statement('g')
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_gate_with_args(self):
        """Test a gate with arguments."""
        text = "g a 1 2.0 -3"
        parser = self.make_parser(start='gate_statement')
        tree = parser.parse(text)
        exp_tree = self.make_gate_statement('g', 'a', 1, 2.0, -3)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_gate_with_array_element(self):
        """Test a gate with an argument that is an element of an array."""
        text = "g q[0]"
        parser = self.make_parser(start='gate_statement')
        tree = parser.parse(text)
        exp_tree = self.make_gate_statement('g', self.make_array_element('q', 0))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_serial_gate_block(self):
        """Test a serial gate block with a separator."""
        text = "{g 0 ; h 1}"
        parser = self.make_parser(start='gate_block')
        tree = parser.parse(text)
        exp_tree = self.make_serial_gate_block(self.make_gate_statement('g', 0), self.make_gate_statement('h', 1))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_serial_gate_block_nosep(self):
        """Test a serial gate block without a separator."""
        text = "{g 0 \n h 1}"
        parser = self.make_parser(start='gate_block')
        tree = parser.parse(text)
        exp_tree = self.make_serial_gate_block(self.make_gate_statement('g', 0), self.make_gate_statement('h', 1))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_parallel_gate_block(self):
        """Test a parallel gate block with a separator."""
        text = "<g 0 | h 1>"
        parser = self.make_parser(start='gate_block')
        tree = parser.parse(text)
        exp_tree = self.make_parallel_gate_block(self.make_gate_statement('g', 0), self.make_gate_statement('h', 1))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_parallel_gate_block_nosep(self):
        """Test a parallel gate block with a separator."""
        text = "<g 0 \n h 1>"
        parser = self.make_parser(start='gate_block')
        tree = parser.parse(text)
        exp_tree = self.make_parallel_gate_block(self.make_gate_statement('g', 0), self.make_gate_statement('h', 1))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_macro_definition(self):
        """Test defining a macro."""
        text = "macro mymacro a b { g a ; h b }"
        parser = self.make_parser(start='macro_definition')
        tree = parser.parse(text)
        gate_block = self.make_serial_gate_block(self.make_gate_statement('g', 'a'), self.make_gate_statement('h', 'b'))
        exp_tree = self.make_macro_statement("mymacro", "a", "b", gate_block)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_loop_statement(self):
        """Test creating a loop."""
        text = "loop 1 { g0 1 }"
        parser = self.make_parser(start='loop_statement')
        tree = parser.parse(text)
        exp_tree = self.make_loop_statement(1, self.make_serial_gate_block(self.make_gate_statement('g0', 1)))
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_header(self):
        """Test a bunch of header statements together."""
        text = "reg q[3]\n" +\
            "map a q[0:3:2]\n" +\
            "let pi 3.14; let reps 100\n"
        parser = self.make_parser(start='header_statements')
        tree = parser.parse(text)
        reg_stmt = self.make_register_statement(self.make_array_declaration('q', 3))
        map_stmt = self.make_map_statement('a', self.make_array_slice('q', 0, 3, 2))
        let0_stmt = self.make_let_statement('pi', 3.14)
        let1_stmt = self.make_let_statement('reps', 100)
        exp_tree = self.make_header_statements(reg_stmt, map_stmt, let0_stmt, let1_stmt)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_body(self):
        """Test a bunch of body statements together"""
        text = "macro foo a b {\n" +\
            "g0 a\n" +\
            "g1 b\n" +\
            "}\n" +\
            "loop 5 < foo q r >\n" +\
            "x q[7]\n"
        parser = self.make_parser(start='body_statements')
        tree = parser.parse(text)
        macro_body = self.make_serial_gate_block(self.make_gate_statement('g0', 'a'),
                                                 self.make_gate_statement('g1', 'b'))
        macro_def = self.make_macro_statement('foo', 'a', 'b', macro_body)
        loop_block = self.make_parallel_gate_block(self.make_gate_statement('foo', 'q', 'r'))
        loop_stmt = self.make_loop_statement(5, loop_block)
        gate_stmt = self.make_gate_statement('x', self.make_array_element('q', 7))
        exp_tree = self.make_body_statements(macro_def, loop_stmt, gate_stmt)
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_nested_blocks(self):
        """Test nested parallel and sequential blocks."""
        text = "{<x a | y b> ; <{z 0 \n w 1}>}"
        parser = self.make_parser(start='sequential_gate_block')
        tree = parser.parse(text)
        exp_tree = self.make_serial_gate_block(
            self.make_parallel_gate_block(
                self.make_gate_statement('x', 'a'),
                self.make_gate_statement('y', 'b')
            ),
            self.make_parallel_gate_block(
                self.make_serial_gate_block(
                    self.make_gate_statement('z', 0),
                    self.make_gate_statement('w', 1)
                )
            )
        )
        act_tree = self.simplify_tree(tree)
        self.assertEqual(exp_tree, act_tree)

    def test_empty_line(self):
        """Test file beginning with empty lines"""
        text = "\nreg q[7]"
        parser = self.make_parser()
        parser.parse(text)

    def test_comment_line(self):
        """Test full line comment"""
        text = "reg q[7]\n// comment\n"
        parser = self.make_parser()
        parser.parse(text)

    def test_line_with_whitespace(self):
        """Test line with whitespace"""
        text = "reg q[7]\n \n"
        parser = self.make_parser()
        parser.parse(text)
