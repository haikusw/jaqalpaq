"""Test that the grammar properly parses Jaqal"""
import unittest
import random

from jaqalpaq.parser.parser import parse_to_sexpression
from jaqalpaq.parser.identifier import Identifier
from jaqalpaq.utilities import RESERVED_WORDS


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

    def test_usepulses_relative(self):
        text = "from .foo.bar usepulses *"
        sexpr = ["circuit", ["usepulses", Identifier.parse(".foo.bar"), "*"]]
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

    def test_subcircuit_gate_block_no_iterations(self):
        text = "subcircuit {\n  g\n  f\n}"
        sexpr = ["circuit", ["subcircuit_block", "", ["gate", "g"], ["gate", "f"]]]
        self.run_test(text, sexpr)

    def test_subcircuit_gate_block_int_iterations(self):
        text = "subcircuit 200 {\n  g\n  f\n}"
        sexpr = ["circuit", ["subcircuit_block", 200, ["gate", "g"], ["gate", "f"]]]
        self.run_test(text, sexpr)

    def test_subcircuit_gate_block_let_iterations(self):
        text = "subcircuit N {\n  g\n  f\n}"
        sexpr = ["circuit", ["subcircuit_block", "N", ["gate", "g"], ["gate", "f"]]]
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

    def test_branch_statement(self):
        """Test creating a branch statement."""
        text = "branch { \n'0100': { g0 1 } \n '1010':{ g1 2} \n}"
        sexpr = [
            "circuit",
            [
                "branch",
                ["case", 0b0100, ["sequential_block", ["gate", "g0", 1]]],
                ["case", 0b1010, ["sequential_block", ["gate", "g1", 2]]],
            ],
        ]
        self.run_test(text, sexpr)

    def test_branch_statement_no_newlines(self):
        """Test creating a branch statement without using newlines."""
        text = "branch { '0100': { g0 1 }; '1010':{ g1 2}; }"
        sexpr = [
            "circuit",
            [
                "branch",
                ["case", 0b0100, ["sequential_block", ["gate", "g0", 1]]],
                ["case", 0b1010, ["sequential_block", ["gate", "g1", 2]]],
            ],
        ]
        self.run_test(text, sexpr)

    def test_branch_statement_no_final_separator(self):
        """Test creating a branch with no separator after the final case."""
        text = "branch { '0100': { g0 1 }; '1010':{ g1 2} }"
        sexpr = [
            "circuit",
            [
                "branch",
                ["case", 0b0100, ["sequential_block", ["gate", "g0", 1]]],
                ["case", 0b1010, ["sequential_block", ["gate", "g1", 2]]],
            ],
        ]
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


class HeaderParserTester(unittest.TestCase):
    """Test parsing just the header from a file."""

    def test_parsing_header(self):
        """Test parsing a header of zero or more statements followed by a body
        of zero or more statements."""
        header_text, header_sexpr = self.make_header()
        body_text, _ = self.make_body()
        text = header_text + body_text
        sexpr = ["circuit"] + header_sexpr
        self.run_test(text, sexpr)

    def make_header(self):
        """Return a header as text and an expected s-expression"""
        text = ""
        sexpr = []
        count = self.make_statement_count()
        for _ in range(count):
            stmt_text, stmt_sexpr = self.make_header_statement()
            text = text + stmt_text + "\n"
            sexpr.append(stmt_sexpr)
        return text, sexpr

    def make_statement_count(self):
        if random.uniform(0, 1) < 0.5:
            return 0
        else:
            return random.randint(1, 5)

    def make_header_statement(self):
        """Return a random header statement."""
        func = random.choice(
            [
                self.make_let_statement,
                self.make_register_statement,
                self.make_map_statement,
                self.make_usepulses_statement,
            ]
        )
        return func()

    def make_let_statement(self):
        """Make a random let statement."""
        ident = self.make_identifier()
        num = self.make_number()
        text = f"let {ident} {num}"
        sexpr = ["let", ident, num]
        return text, sexpr

    def make_register_statement(self):
        """Make a random register statement."""
        ident = self.make_identifier()
        size = self.make_integer()
        text = f"register {ident}[{size}]"
        sexpr = ["register", ident, size]
        return text, sexpr

    def make_map_statement(self):
        """Make a random map statement."""
        # For simplicity we'll just do a whole-register map
        dst_ident = self.make_identifier()
        src_ident = self.make_identifier()
        text = f"map {dst_ident} {src_ident}"
        sexpr = ["map", dst_ident, src_ident]
        return text, sexpr

    def make_usepulses_statement(self):
        """Make a random usepulses statement."""
        module = self.make_identifier()
        filename = self.make_identifier()
        text = f"from {module}.{filename} usepulses *"
        sexpr = ["usepulses", Identifier.parse(f"{module}.{filename}"), "*"]
        return text, sexpr

    def make_identifier(self):
        """Return a random identifier."""
        # This is a subset of possible identifiers since that's not
        # really what we're testing here.
        while True:
            count = random.randint(1, 8)
            letters = random.choices(
                [chr(c) for c in range(ord("a"), ord("z") + 1)], k=count
            )
            ident = "".join(letters)
            if ident not in RESERVED_WORDS:
                return ident

    def make_number(self):
        """Return a random number, either an integer or float."""
        select = random.uniform(0, 1)
        if select < 0.5:
            return random.randint(-100, 100)
        elif select < 0.6:
            return float(random.randint(-100, 100))
        else:
            return self.make_float()

    def make_integer(self):
        return random.randint(1, 100)

    def make_float(self):
        return random.uniform(-100, 100)

    def make_body(self):
        text = ""
        sexpr = []
        count = self.make_statement_count()
        for _ in range(count):
            stmt_text, stmt_sexpr = self.make_body_statement()
            text = text + stmt_text + "\n"
            sexpr.append(stmt_sexpr)
        return text, sexpr

    def make_body_statement(self):
        func = random.choice(
            [
                self.make_gate,
                self.make_macro,
                self.make_parallel_block,
                self.make_sequential_block,
                self.make_loop,
            ]
        )
        return func()

    def make_gate(self):
        """Make a random gate."""
        arg_count = random.randint(0, 4)
        name = self.make_identifier()
        args = [self.make_gate_arg() for _ in range(arg_count)]
        text = f'{name} {" ".join(str(arg) for arg in args)}'
        sexpr = ["gate", name, *args]
        return text, sexpr

    def make_gate_arg(self):
        if random.uniform(0, 1) < 0.5:
            return self.make_identifier()
        else:
            return self.make_number()

    def make_macro(self):
        """Make a random macro definition."""
        param_count = random.randint(0, 4)
        name = self.make_identifier()
        params = [self.make_identifier() for _ in range(param_count)]
        block_text, block_sexpr = self.make_sequential_block()
        param_string = " ".join(str(param) for param in params)
        text = f"macro {name} {param_string} {block_text}"
        sexpr = ["macro", name, *params, block_sexpr]
        return text, sexpr

    def make_sequential_block(self):
        gate_count = random.randint(0, 4)
        gates = [self.make_gate() for _ in range(gate_count)]
        gate_string = ";".join(g[0] for g in gates)
        text = f"{{ {gate_string} }}"
        sexpr = ["sequential_block", *[g[1] for g in gates]]
        return text, sexpr

    def make_parallel_block(self):
        gate_count = random.randint(0, 4)
        gates = [self.make_gate() for _ in range(gate_count)]
        gate_string = "|".join(g[0] for g in gates)
        text = f"< {gate_string} >"
        sexpr = ["parallel_block", *[g[1] for g in gates]]
        return text, sexpr

    def make_loop(self):
        count = random.randint(0, 10)
        block_text, block_sexpr = self.make_sequential_block()
        text = f"loop {count} {block_text}"
        sexpr = ["loop", count, block_sexpr]
        return text, sexpr

    def run_test(self, text, exp_sexpr):
        act_sexpr = parse_to_sexpression(text, header_only=True)
        self.assertEqual(exp_sexpr, act_sexpr)


if __name__ == "__main__":
    unittest.main()
