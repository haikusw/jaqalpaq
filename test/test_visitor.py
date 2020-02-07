from unittest import TestCase
import pathlib

from jaqal.parse import *


# Accommodate both running from the test directory (as PyCharm does) and running from the project root.

top_grammar_filename = 'jaqal/jaqal_grammar.lark'
test_grammar_filename = '../jaqal/jaqal_grammar.lark'

if pathlib.Path(top_grammar_filename).exists():
    grammar_filename = top_grammar_filename
elif pathlib.Path(test_grammar_filename):
    grammar_filename = test_grammar_filename
else:
    raise IOError('Cannot find grammar file')


class TestVisitor(ParseTreeVisitor):

    def visit_program(self, header_statements, body_statements):
        return {'type': 'program', 'header_statements': header_statements, 'body_statements': body_statements}

    def visit_register_statement(self, array_declaration):
        return {'type': 'register_statement', 'array_declaration': array_declaration}

    def visit_map_statement(self, target, source):
        return {'type': 'map_statement', 'target': target, 'source': source}

    def visit_let_statement(self, identifier, number):
        return {'type': 'let_statement', 'identifier': identifier, 'number': number}

    def visit_gate_statement(self, gate_name, gate_args):
        return {'type': 'gate_statement', 'gate_name': gate_name, 'gate_args': gate_args}

    def visit_macro_definition(self, name, arguments, block):
        return {'type': 'macro_definition', 'name': name, 'arguments': arguments, 'block': block}

    def visit_macro_gate_block(self, block):
        return {'type': 'macro_gate_block', 'block': block}

    def visit_loop_statement(self, repetition_count, block):
        return {'type': 'loop_statement', 'repetition_count': repetition_count, 'block': block}

    def visit_sequential_gate_block(self, statements):
        return {'type': 'sequential_gate_block', 'statements': statements}

    def visit_parallel_gate_block(self, statements):
        return {'type': 'parallel_gate_block', 'statements': statements}

    def visit_array_declaration(self, identifier, size):
        return {'type': 'array_declaration', 'identifier': identifier, 'size': size}

    def visit_array_element(self, identifier, index):
        return {'type': 'array_element', 'identifier': identifier, 'index': index}

    def visit_array_slice(self, identifier, index_slice):
        return {'type': 'array_slice', 'identifier': identifier, 'index_slice': index_slice}

    def visit_let_identifier(self, identifier):
        return identifier

    def visit_let_or_map_identifier(self, identifier):
        return identifier


class ParseTreeVisitorTester(TestCase):

    def make_parser(self, *args, **kwargs) -> Lark:
        with open(grammar_filename, 'r') as fd:
            kwargs['parser'] = 'lalr'
            return Lark(fd, *args, **kwargs)

    def test_array_declaration(self):
        """Test visiting an array declaration."""
        text = 'foo[42]'
        parser = self.make_parser(start='array_declaration')
        tree = parser.parse(text)
        visitor = TestVisitor()
        exp_result = {'type': 'array_declaration', 'identifier': 'foo', 'size': 42}
        act_result = visitor.visit(tree)
        self.assertEqual(exp_result, act_result)

    def test_array_element(self):
        """Test visiting an array element."""
        text = 'foo[42]'
        parser = self.make_parser(start='array_element')
        tree = parser.parse(text)
        visitor = TestVisitor()
        exp_result = {'type': 'array_element', 'identifier': 'foo', 'index': 42}
        act_result = visitor.visit(tree)
        self.assertEqual(exp_result, act_result)

    def test_array_slice(self):
        """Test visiting an array slice."""
        cases = [
            ('foo[42:]', ('foo', slice(42, None, None))),
            ('foo[:42]', ('foo', slice(None, 42, None))),
            ('foo[:]', ('foo', slice(None, None, None))),
            ('foo[::]', ('foo', slice(None, None, None))),
            ('foo[::2]', ('foo', slice(None, None, 2))),
            ('foo[-1::-2]', ('foo', slice(-1, None, -2))),
            ('foo[0:42]', ('foo', slice(0, 42))),
            ('foo[a:3:-1]', ('foo', slice('a', 3, -1)))
        ]
        parser = self.make_parser(start='array_slice')
        visitor = TestVisitor()
        for text, (identifier, index_slice) in cases:
            tree = parser.parse(text)
            exp_result = {'type': 'array_slice', 'identifier': identifier, 'index_slice': index_slice}
            act_result = visitor.visit(tree)
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_register_statement(self):
        """Test visiting a register statement."""
        cases = [
            ('register q[9]', ('q', 9)),
            ('register foo [ abc ]', ('foo', 'abc'))
        ]
        parser = self.make_parser(start='register_statement')
        visitor = TestVisitor()
        for text, (identifier, size) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {'type': 'register_statement', 'array_declaration': {'type': 'array_declaration', 'identifier': identifier, 'size': size}}
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_map_statement(self):
        """Test visiting a map statement."""
        cases = [
            ('map a b', ('a', 'b')),
            ('map q r[0:4:2]', ('q',
                                {'type': 'array_slice', 'identifier': 'r', 'index_slice': slice(0, 4, 2)}))
        ]
        parser = self.make_parser(start='map_statement')
        visitor = TestVisitor()
        for text, (target, source) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {'type': 'map_statement', 'target': target, 'source': source}
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_let_statement(self):
        """Test visiting a let statement"""
        cases = [
            ('let pi 3.14', ('pi', 3.14)),
            ('let a -1', ('a', -1))
        ]
        parser = self.make_parser(start='let_statement')
        visitor = TestVisitor()
        for text, (identifier, number) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {'type': 'let_statement', 'identifier': identifier, 'number': number}
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_gate_statement(self):
        """Test visiting a gate statement."""
        cases = [
            ('foo 42 43', ('foo', [42, 43])),
            ('bar a[2]', ('bar', [{'type': 'array_element', 'identifier': 'a', 'index': 2}]))
        ]
        parser = self.make_parser(start='gate_statement')
        visitor = TestVisitor()
        for text, (gate_name, gate_args) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {'type': 'gate_statement', 'gate_name': gate_name, 'gate_args': gate_args}
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_sequential_gate_block(self):
        """Test visiting a sequential gate block."""
        cases = [
            ('{g0 a b; g1 1 2 3;g3}', [('g0', ['a', 'b']), ('g1', [1, 2, 3]), ('g3', [])]),
            ('{foo\nbar}', [('foo', []), ('bar', [])]),
            ('{foo a[5]}', [('foo', [{'type': 'array_element', 'identifier': 'a', 'index': 5}])])
        ]
        parser = self.make_parser(start='sequential_gate_block')
        visitor = TestVisitor()
        for text, gate_statements in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {'type': 'sequential_gate_block',
                          'statements': [{'type': 'gate_statement', 'gate_name': gate_name, 'gate_args': gate_args}
                                         for gate_name, gate_args in gate_statements]}
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_parallel_gate_block(self):
        """Test visiting a parallel gate block."""
        cases = [
            ('<g0 a b| g1 1 2 3|g3>', [('g0', ['a', 'b']), ('g1', [1, 2, 3]), ('g3', [])]),
            ('<foo\nbar>', [('foo', []), ('bar', [])]),
            ('<foo a[5]>', [('foo', [{'type': 'array_element', 'identifier': 'a', 'index': 5}])])
        ]
        parser = self.make_parser(start='parallel_gate_block')
        visitor = TestVisitor()
        for text, gate_statements in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {'type': 'parallel_gate_block',
                          'statements': [{'type': 'gate_statement', 'gate_name': gate_name, 'gate_args': gate_args}
                                         for gate_name, gate_args in gate_statements]}
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_macro_definition(self):
        """Test visiting a macro definition."""
        cases = [
            ('macro foo a b {g0 a b}', ('foo', ['a', 'b'],
                                        {'type': 'macro_gate_block',
                                         'block': {'type': 'sequential_gate_block',
                                                   'statements': [{'type': 'gate_statement', 'gate_name': 'g0',
                                                                   'gate_args': ['a', 'b']}]}}))
        ]
        parser = self.make_parser(start='macro_definition')
        visitor = TestVisitor()
        for text, (name, arguments, block) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {'type': 'macro_definition', "name": name, 'arguments': arguments, 'block': block}
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_loop_statement(self):
        """Test visiting a loop statement."""
        cases = [
            ('loop 3 {g0 a b}', (3, {'type': 'sequential_gate_block',
                                     'statements': [{'type': 'gate_statement',
                                                     'gate_name': 'g0', 'gate_args': ['a', 'b']}]}))
        ]
        parser = self.make_parser(start='loop_statement')
        visitor = TestVisitor()
        for text, (repetition_count, block) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {'type': 'loop_statement', 'repetition_count': repetition_count, 'block': block}
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_program(self):
        """Test visiting a program at the top level"""
        cases = [
            ('register q[3]\ng0 a b',
             {
                 'type': 'program',
                 'header_statements': [
                     {
                         'type': 'register_statement',
                         'array_declaration': {
                             'type': 'array_declaration',
                             'identifier': 'q',
                             'size': 3
                         }
                     }
                 ],
                 'body_statements': [
                     {
                         'type': 'gate_statement',
                         'gate_name': 'g0',
                         'gate_args': ['a', 'b']
                     }
                 ]
             })
        ]
        parser = self.make_parser(start='start')
        visitor = TestVisitor()
        for text, exp_result in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")


class TreeRewriteTester(TestCase):
    """Tests for basic functionality of the TreeRewriteVisitor base class. All tests compare the tree against its
    transformed self, which should be identical."""

    def make_parser(self, *, start):
        return make_lark_parser(start=start)

    def run_tests(self, texts, parser):
        for text in texts:
            tree = parser.parse(text)
            rw_tree = self.visitor.visit(tree)
            self.assertEqual(tree, rw_tree)
            self.assertIsNot(tree, rw_tree)

    def setUp(self):
        self.visitor = TreeRewriteVisitor()

    def test_register_statement(self):
        parser = self.make_parser(start='register_statement')
        texts = [
            'register r[1]',
            'register QASDF[abc]'
        ]
        self.run_tests(texts, parser)

    def test_map_statement(self):
        parser = self.make_parser(start='map_statement')
        texts = [
            'map a b',
            'map q r[0:5:2]'
        ]
        self.run_tests(texts, parser)

    def test_let_statement(self):
        parser = self.make_parser(start='let_statement')
        texts = [
            'let pi 3.14',
            'let q 5'
        ]
        self.run_tests(texts, parser)

    def test_gate_statement(self):
        parser = self.make_parser(start='gate_statement')
        texts = [
            'g0 a b',
            'foo',
            'h r[5]',
            'r 1.23'
        ]
        self.run_tests(texts, parser)

    def test_macro_definition(self):
        parser = self.make_parser(start='macro_definition')
        texts = [
            'macro foo {}',
            'macro foo {bar}',
            'macro foo a b {g a b}',
            'macro foo <>',
            'macro foo <bar>'
        ]
        self.run_tests(texts, parser)

    def test_loop_statement(self):
        parser = self.make_parser(start='loop_statement')
        texts = [
            'loop 5 {}',
            'loop 77 {g; h}',
            'loop COUNT {foo}'
        ]
        self.run_tests(texts, parser)

    def test_sequential_gate_block(self):
        parser = self.make_parser(start='sequential_gate_block')
        texts = [
            '{}',
            '{foo}',
            '{foo\nbar}',
            '{foo;bar;baz}',
            '{foo ; <a | b>}'
        ]
        self.run_tests(texts, parser)

    def test_parallel_gate_block(self):
        parser = self.make_parser(start='parallel_gate_block')
        texts = [
            '<>',
            '<foo>',
            '<foo\nbar>',
            '<foo|bar|baz>',
            '<foo | {a ; b}>'
        ]
        self.run_tests(texts, parser)

    def test_array_declaration(self):
        parser = self.make_parser(start='array_declaration')
        texts = [
            'g[2]',
            'foo[bar]'
        ]
        self.run_tests(texts, parser)

    def test_array_element(self):
        parser = self.make_parser(start='array_element')
        texts = [
            'g[2]',
            'foo[bar]'
        ]
        self.run_tests(texts, parser)

    def test_array_slice(self):
        parser = self.make_parser(start='array_slice')
        texts = [
            'a[:5]',
            'a[5:]',
            'a[::22]',
            'a[-1::-2]',
            'a[0:5]',
            'b[5:3:-1]',
            'c[a:b]'
        ]
        self.run_tests(texts, parser)

    def test_program(self):
        parser = self.make_parser(start='start')
        texts = [
            'register r[3]; g a b'
        ]
        self.run_tests(texts, parser)