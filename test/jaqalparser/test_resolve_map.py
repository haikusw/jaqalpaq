from unittest import TestCase

from jaqalpaq.parser.resolve_map import resolve_map
from .helpers.parser import ParserTesterMixin
from jaqalpaq.parser.parse import make_lark_parser
from jaqalpaq.parser.extract_map import extract_map


class ResolveMapTester(ParserTesterMixin, TestCase):
    def test_map_full_register(self):
        """Test mapping a full register and accessing a single array element."""
        setup_text = "register r[7]; map a r"
        gate_text = "foo a[1]"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement("foo", self.make_array_element_qual("r", 1))
            ),
        )
        self.run_test(setup_text, gate_text, exp_result)

    def test_map_slice(self):
        """Test mapping a slice of a register."""
        setup_text = "register r[7]; map a r[1:7:2]"
        gate_text = "foo a[1]"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement("foo", self.make_array_element_qual("r", 3))
            ),
        )
        self.run_test(setup_text, gate_text, exp_result)

    def test_map_single_element(self):
        """Test mapping a single element of a register."""
        setup_text = "register r[7]; map a r[1]"
        gate_text = "foo a"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement("foo", self.make_array_element_qual("r", 1))
            ),
        )
        self.run_test(setup_text, gate_text, exp_result)

    def test_remap_full_register(self):
        """Test mapping a full register, then remapping that map and accessing a single array element."""
        setup_text = "register r[7]; map b r; map a b"
        gate_text = "foo a[1]"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement("foo", self.make_array_element_qual("r", 1))
            ),
        )
        self.run_test(setup_text, gate_text, exp_result)

    def test_remap_slice(self):
        """Test mapping a slice of a register then remapping that slice."""
        setup_text = "register r[7]; map b r[1:7]; map a b[::2]"
        gate_text = "foo a[1]"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement("foo", self.make_array_element_qual("r", 3))
            ),
        )
        self.run_test(setup_text, gate_text, exp_result)

    def test_remap_single_element(self):
        """Test mapping a single element, then remapping that entire mapping."""
        setup_text = "register r[7]; map b r[1]; map a b"
        gate_text = "foo a"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_gate_statement("foo", self.make_array_element_qual("r", 1))
            ),
        )
        self.run_test(setup_text, gate_text, exp_result)

    def test_forbid_nonexistent_mapping(self):
        """Test that we throw an error when attempting to map to a nonexistent register."""
        setup_text = "register r[7]; map a q[1]"
        gate_text = "foo a"
        with self.assertRaises(Exception):
            parser = make_lark_parser()
            map_dict, register_dict = extract_map(parser.parse(setup_text))
            resolve_map(parser.parse(gate_text), map_dict, register_dict)

    def test_forbid_mapping_whole_register(self):
        """Test that we throw an error when using a mapping in a context where a register element is expected."""
        setup_text = "register r[7]; map a r"
        gate_text = "foo a"
        with self.assertRaises(Exception):
            parser = make_lark_parser()
            map_dict, register_dict = extract_map(parser.parse(setup_text))
            resolve_map(parser.parse(gate_text), map_dict, register_dict)

    def test_inside_macro_definition(self):
        """Check that a map value inside a macro definition is properly expanded."""
        setup_text = "register r[7]; map a r"
        text = "macro foo { g a[2] }"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_macro_statement(
                    "foo",
                    self.make_serial_gate_block(
                        self.make_gate_statement(
                            "g", self.make_array_element_qual("r", 2)
                        )
                    ),
                )
            ),
        )
        self.run_test(setup_text, text, exp_result)

    def test_inside_macro_definition_shadowed(self):
        """Test that a map value does not expand inside a macro definition if it shadows a macro
        parameter."""
        setup_text = "register r[7]; map a r[0]"
        text = "macro foo a { g a }"
        exp_result = self.make_program(
            self.make_header_statements(),
            self.make_body_statements(
                self.make_macro_statement(
                    "foo",
                    "a",
                    self.make_serial_gate_block(
                        self.make_gate_statement("g", self.make_gate_arg("a"))
                    ),
                )
            ),
        )
        self.run_test(setup_text, text, exp_result)

    def run_test(self, setup_text, gate_text, exp_result):
        parser = make_lark_parser()
        map_dict, register_dict = extract_map(parser.parse(setup_text))
        act_tree = resolve_map(parser.parse(gate_text), map_dict, register_dict)
        act_result = self.simplify_tree(act_tree)
        self.assertEqual(exp_result, act_result)
