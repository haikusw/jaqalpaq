from unittest import TestCase
import pathlib

from jaqalpaq.parser.tree import *


# Accommodate both running from the test directory (as PyCharm does) and running from the project root.

top_grammar_filename = "jaqal/jaqal_grammar.lark"
test_grammar_filename = "../jaqal/jaqal_grammar.lark"

if pathlib.Path(top_grammar_filename).exists():
    grammar_filename = top_grammar_filename
elif pathlib.Path(test_grammar_filename):
    grammar_filename = test_grammar_filename
else:
    raise IOError("Cannot find grammar file")


class Visitor(ParseTreeVisitor):
    def visit_program(self, header_statements, body_statements):
        return {
            "type": "program",
            "header_statements": header_statements,
            "body_statements": body_statements,
        }

    def visit_register_statement(self, array_declaration):
        return {"type": "register_statement", "array_declaration": array_declaration}

    def visit_map_statement(self, target, source):
        return {"type": "map_statement", "target": target, "source": source}

    def visit_let_statement(self, identifier, number):
        return {"type": "let_statement", "identifier": identifier, "number": number}

    def visit_usepulses_statement(self, identifier, objects):
        return {
            "type": "usepulses_statement",
            "identifier": identifier,
            "objects": objects,
        }

    def visit_gate_statement(self, gate_name, gate_args):
        return {
            "type": "gate_statement",
            "gate_name": gate_name,
            "gate_args": gate_args,
        }

    def visit_macro_definition(self, name, arguments, block):
        return {
            "type": "macro_definition",
            "name": name,
            "arguments": arguments,
            "block": block,
        }

    def visit_macro_gate_block(self, block):
        return {"type": "macro_gate_block", "block": block}

    def visit_loop_statement(self, repetition_count, block):
        return {
            "type": "loop_statement",
            "repetition_count": repetition_count,
            "block": block,
        }

    def visit_sequential_gate_block(self, statements):
        return {"type": "sequential_gate_block", "statements": statements}

    def visit_parallel_gate_block(self, statements):
        return {"type": "parallel_gate_block", "statements": statements}

    def visit_array_declaration(self, identifier, size):
        return {"type": "array_declaration", "identifier": identifier, "size": size}

    def visit_array_element(self, identifier, index):
        return {"type": "array_element", "identifier": identifier, "index": index}

    def visit_array_element_qual(self, identifier, index):
        return {"type": "array_element_qual", "identifier": identifier, "index": index}

    def visit_array_slice(self, identifier, index_slice):
        return {
            "type": "array_slice",
            "identifier": identifier,
            "index_slice": index_slice,
        }

    def visit_qualified_identifier(self, names):
        return names

    def visit_let_identifier(self, identifier):
        return identifier

    def visit_let_or_map_identifier(self, identifier):
        return identifier


class ParseTreeVisitorTester(TestCase):
    def make_parser(self, *args, **kwargs) -> Lark:
        return make_lark_parser(*args, **kwargs)

    def test_array_declaration(self):
        """Test visiting an array declaration."""
        text = "foo[42]"
        parser = self.make_parser(start="array_declaration")
        tree = parser.parse(text)
        visitor = Visitor()
        exp_result = {"type": "array_declaration", "identifier": "foo", "size": 42}
        act_result = visitor.visit(tree)
        self.assertEqual(exp_result, act_result)

    def test_array_element(self):
        """Test visiting an array element."""
        text = "foo[42]"
        parser = self.make_parser(start="array_element")
        tree = parser.parse(text)
        visitor = Visitor()
        exp_result = {"type": "array_element", "identifier": "foo", "index": 42}
        act_result = visitor.visit(tree)
        self.assertEqual(exp_result, act_result)

    def test_array_slice(self):
        """Test visiting an array slice."""
        cases = [
            ("foo[42:]", ("foo", slice(42, None, None))),
            ("foo[:42]", ("foo", slice(None, 42, None))),
            ("foo[:]", ("foo", slice(None, None, None))),
            ("foo[::]", ("foo", slice(None, None, None))),
            ("foo[::2]", ("foo", slice(None, None, 2))),
            ("foo[-1::-2]", ("foo", slice(-1, None, -2))),
            ("foo[0:42]", ("foo", slice(0, 42))),
            ("foo[a:3:-1]", ("foo", slice(("a",), 3, -1))),
        ]
        parser = self.make_parser(start="array_slice")
        visitor = Visitor()
        for text, (identifier, index_slice) in cases:
            tree = parser.parse(text)
            exp_result = {
                "type": "array_slice",
                "identifier": identifier,
                "index_slice": index_slice,
            }
            act_result = visitor.visit(tree)
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_register_statement(self):
        """Test visiting a register statement."""
        cases = [
            ("register q[9]", ("q", 9)),
            ("register foo [ abc ]", ("foo", ("abc",))),
        ]
        parser = self.make_parser(start="register_statement")
        visitor = Visitor()
        for text, (identifier, size) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {
                "type": "register_statement",
                "array_declaration": {
                    "type": "array_declaration",
                    "identifier": identifier,
                    "size": size,
                },
            }
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_map_statement(self):
        """Test visiting a map statement."""
        cases = [
            ("map a b", ("a", "b")),
            (
                "map q r[0:4:2]",
                (
                    "q",
                    {
                        "type": "array_slice",
                        "identifier": "r",
                        "index_slice": slice(0, 4, 2),
                    },
                ),
            ),
        ]
        parser = self.make_parser(start="map_statement")
        visitor = Visitor()
        for text, (target, source) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {"type": "map_statement", "target": target, "source": source}
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_let_statement(self):
        """Test visiting a let statement"""
        cases = [("let pi 3.14", ("pi", 3.14)), ("let a -1", ("a", -1))]
        parser = self.make_parser(start="let_statement")
        visitor = Visitor()
        for text, (identifier, number) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {
                "type": "let_statement",
                "identifier": identifier,
                "number": number,
            }
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_gate_statement(self):
        """Test visiting a gate statement."""
        cases = [
            ("foo 42 43", ("foo", [42, 43])),
            (
                "bar a[2]",
                (
                    "bar",
                    [{"type": "array_element_qual", "identifier": ("a",), "index": 2}],
                ),
            ),
        ]
        parser = self.make_parser(start="gate_statement")
        visitor = Visitor()
        for text, (gate_name, gate_args) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {
                "type": "gate_statement",
                "gate_name": (gate_name,),
                "gate_args": gate_args,
            }
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_sequential_gate_block(self):
        """Test visiting a sequential gate block."""
        cases = [
            (
                "{g0 a b; g1 1 2 3;g3}",
                [(("g0",), [("a",), ("b",)]), (("g1",), [1, 2, 3]), (("g3",), [])],
            ),
            ("{foo\nbar}", [(("foo",), []), (("bar",), [])]),
            (
                "{foo a[5]}",
                [
                    (
                        ("foo",),
                        [
                            {
                                "type": "array_element_qual",
                                "identifier": ("a",),
                                "index": 5,
                            }
                        ],
                    )
                ],
            ),
        ]
        parser = self.make_parser(start="sequential_gate_block")
        visitor = Visitor()
        for text, gate_statements in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {
                "type": "sequential_gate_block",
                "statements": [
                    {
                        "type": "gate_statement",
                        "gate_name": gate_name,
                        "gate_args": gate_args,
                    }
                    for gate_name, gate_args in gate_statements
                ],
            }
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_parallel_gate_block(self):
        """Test visiting a parallel gate block."""
        cases = [
            (
                "<g0 a b| g1 1 2 3|g3>",
                [(("g0",), [("a",), ("b",)]), (("g1",), [1, 2, 3]), (("g3",), [])],
            ),
            ("<foo\nbar>", [(("foo",), []), (("bar",), [])]),
            (
                "<foo a[5]>",
                [
                    (
                        ("foo",),
                        [
                            {
                                "type": "array_element_qual",
                                "identifier": ("a",),
                                "index": 5,
                            }
                        ],
                    )
                ],
            ),
        ]
        parser = self.make_parser(start="parallel_gate_block")
        visitor = Visitor()
        for text, gate_statements in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {
                "type": "parallel_gate_block",
                "statements": [
                    {
                        "type": "gate_statement",
                        "gate_name": gate_name,
                        "gate_args": gate_args,
                    }
                    for gate_name, gate_args in gate_statements
                ],
            }
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_macro_definition(self):
        """Test visiting a macro definition."""
        cases = [
            (
                "macro foo a b {g0 a b}",
                (
                    "foo",
                    ["a", "b"],
                    {
                        "type": "macro_gate_block",
                        "block": {
                            "type": "sequential_gate_block",
                            "statements": [
                                {
                                    "type": "gate_statement",
                                    "gate_name": ("g0",),
                                    "gate_args": [("a",), ("b",)],
                                }
                            ],
                        },
                    },
                ),
            )
        ]
        parser = self.make_parser(start="macro_definition")
        visitor = Visitor()
        for text, (name, arguments, block) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {
                "type": "macro_definition",
                "name": name,
                "arguments": arguments,
                "block": block,
            }
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_loop_statement(self):
        """Test visiting a loop statement."""
        cases = [
            (
                "loop 3 {g0 a b}",
                (
                    3,
                    {
                        "type": "sequential_gate_block",
                        "statements": [
                            {
                                "type": "gate_statement",
                                "gate_name": ("g0",),
                                "gate_args": [("a",), ("b",)],
                            }
                        ],
                    },
                ),
            )
        ]
        parser = self.make_parser(start="loop_statement")
        visitor = Visitor()
        for text, (repetition_count, block) in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            exp_result = {
                "type": "loop_statement",
                "repetition_count": repetition_count,
                "block": block,
            }
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")

    def test_program(self):
        """Test visiting a program at the top level"""
        cases = [
            (
                "register q[3]\ng0 a b",
                {
                    "type": "program",
                    "header_statements": [
                        {
                            "type": "register_statement",
                            "array_declaration": {
                                "type": "array_declaration",
                                "identifier": "q",
                                "size": 3,
                            },
                        }
                    ],
                    "body_statements": [
                        {
                            "type": "gate_statement",
                            "gate_name": ("g0",),
                            "gate_args": [("a",), ("b",)],
                        }
                    ],
                },
            )
        ]
        parser = self.make_parser(start="start")
        visitor = Visitor()
        for text, exp_result in cases:
            tree = parser.parse(text)
            act_result = visitor.visit(tree)
            self.assertEqual(exp_result, act_result, f"Failed to parse {text}")


class VisitorWithPosition(Visitor):
    """Like the test visitor but also include position information."""

    def add_position(self, dictionary):
        dictionary['pos'] = self.current_pos
        dictionary['line'] = self.current_line
        dictionary['column'] = self.current_column
        return dictionary

    def visit_program(self, *args):
        return self.add_position(super().visit_program(*args))

    def visit_register_statement(self, *args):
        return self.add_position(super().visit_register_statement(*args))

    def visit_map_statement(self, *args):
        return self.add_position(super().visit_map_statement(*args))

    def visit_let_statement(self, *args):
        return self.add_position(super().visit_let_statement(*args))

    def visit_usepulses_statement(self, *args):
        return self.add_position(super().visit_usepulses_statement(*args))

    def visit_gate_statement(self, *args):
        return self.add_position(super().visit_gate_statement(*args))

    def visit_macro_definition(self, *args):
        return self.add_position(super().visit_macro_definition(*args))

    def visit_macro_gate_block(self, *args):
        return self.add_position(super().visit_macro_gate_block(*args))

    def visit_loop_statement(self, *args):
        return self.add_position(super().visit_loop_statement(*args))

    def visit_sequential_gate_block(self, *args):
        return self.add_position(super().visit_sequential_gate_block(*args))

    def visit_parallel_gate_block(self, *args):
        return self.add_position(super().visit_parallel_gate_block(*args))

    def visit_array_declaration(self, *args):
        return self.add_position(super().visit_array_declaration(*args))

    def visit_array_element(self, *args):
        return self.add_position(super().visit_array_element(*args))

    def visit_array_element_qual(self, *args):
        return self.add_position(super().visit_array_element_qual(*args))

    def visit_array_slice(self, *args):
        return self.add_position(super().visit_array_slice(*args))


class PositionTester(TestCase):

    def test_positions(self):
        text = "from mypulses.myclass usepulses *\n"\
            "register r[3]\n"\
            "\n"\
            "map a r[0]\n"\
            "\n"\
            "let pi 3.14\n"\
            "\n"\
            "macro foo a {\n"\
            "  g0 a\n"\
            "}\n"\
            "\n"\
            "{ g1 ; g2 r[0] }\n"\
            "<\n"\
            "  foo pi\n"\
            "  g3\n"\
            ">\n"

        parser = make_lark_parser(start="start")
        visitor = VisitorWithPosition()
        tree = visitor.visit(parser.parse(text))

        usepulses_entry = self.find_entry('usepulses_statement', tree)
        usepulses_start = 0
        self.check_positions(usepulses_entry, range(usepulses_start, usepulses_start + 34), range(1, 2), range(0, 34))

        register_entry = self.find_entry('register_statement', tree)
        register_start = text.find('register')
        self.check_positions(register_entry, range(register_start, register_start + 14), range(2, 3), range(0, 14))

        map_entry = self.find_entry('map_statement', tree)
        map_start = text.find('map')
        self.check_positions(
            map_entry,
            range(map_start, map_start + 11),
            range(4, 5),
            range(0, 11))

        let_entry = self.find_entry('let_statement', tree)
        let_start = text.find('let')
        self.check_positions(
            let_entry,
            range(let_start, let_start + 12),
            range(6, 7),
            range(0, 12))

        macro_entry = self.find_entry('macro_definition', tree)
        macro_start = text.find('macro')
        macro_end = text.find('\n}\n') + 1
        self.check_positions(
            macro_entry,
            range(macro_start, macro_end + 1),
            range(8, 11),
            range(0, 14))

        sequential_block_entry = self.find_entry('sequential_gate_block', tree)
        sequential_start = text.find("\n{")
        self.check_positions(
            sequential_block_entry,
            range(sequential_start, sequential_start + 17),
            range(12, 13),
            range(0, 17))

        parallel_block_entry = self.find_entry('parallel_gate_block', tree)
        parallel_start = text.find('<')
        parallel_end = text.find('>') + 1
        self.check_positions(
            parallel_block_entry,
            range(parallel_start, parallel_end),
            range(13, 17),
            range(0, 9))

    def find_entry(self, entry_type, tree):
        return self.find_entries(entry_type, tree)[0]

    def find_entries(self, entry_type, tree):
        entries = []
        if tree['type'] == entry_type:
            entries.append(tree)
        for field, value in tree.items():
            if isinstance(value, list):
                for subtree in value:
                    if isinstance(subtree, dict):
                        entries.extend(self.find_entries(entry_type, subtree))
        return entries

    def check_positions(self, entry, exp_pos_range, exp_line_range,
                        exp_column_range):
        """Given a dictionary entry, make sure all position data falls in the
        expected range."""

        self.assertIn(entry['pos'], exp_pos_range)
        self.assertIn(entry['line'], exp_line_range)
        self.assertIn(entry['column'], exp_column_range)
