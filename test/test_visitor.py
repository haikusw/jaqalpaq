from unittest import TestCase

from lark import Lark

from iqasm.parse import *

grammar_filename = '../iqasm/iqasm_grammar.lark'


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
        # TODO: I realize now the semantics is a bit wrong. This should be fixed in a future issue.
        cases = [
            ('foo[42]', ('foo', slice(42))),
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
            ('reg q[9]', ('q', 9)),
            ('reg foo [ abc ]', ('foo', 'abc'))
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
            ('map q[2] r[0:4:2]', ({'type': 'array_declaration', 'identifier': 'q', 'size': 2},
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
                                        {'type': 'sequential_gate_block',
                                         'statements': [{'type': 'gate_statement', 'gate_name': 'g0',
                                                         'gate_args': ['a', 'b']}]}))
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
            ('reg q[3]\ng0 a b',
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
            print(tree)
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")
