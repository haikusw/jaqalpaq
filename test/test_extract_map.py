from unittest import TestCase

from jaqal.parse import TreeManipulators
from jaqal.identifier import Identifier
from jaqal.parse import make_lark_parser
from jaqal.extract_map import extract_map


class ExtractMapTester(TestCase):

    def test_map_whole_register(self):
        text = "register q[5]; map a q"
        exp_result = {Identifier('a'): TreeManipulators.make_identifier('q')}
        self.run_test(text, exp_result)

    def test_map_single_index(self):
        text = "register q[5]; map a q[1]"
        exp_result = {
            Identifier('a'): TreeManipulators.make_array_element(
                TreeManipulators.make_identifier('q'),
                TreeManipulators.make_integer(1))
        }
        self.run_test(text, exp_result)

    def test_map_range(self):
        text = "register q[5]; map a q[1:4:2]"
        exp_result = {
            Identifier('a'): TreeManipulators.make_array_slice(
                TreeManipulators.make_identifier('q'),
                slice(TreeManipulators.make_integer(1), TreeManipulators.make_integer(4), TreeManipulators.make_integer(2)))
        }
        self.run_test(text, exp_result)

    def test_map_existing_alias(self):
        text = "register q[5]; map a q; map b a"
        exp_result = {Identifier('a'): TreeManipulators.make_identifier('q'),
                      Identifier('b'): TreeManipulators.make_identifier('a')}
        self.run_test(text, exp_result)

    def test_no_existing_register(self):
        text = "map a q"
        parser = make_lark_parser()
        tree = parser.parse(text)
        with self.assertRaises(Exception):
            extract_map(tree)

    def run_test(self, text, exp_result):
        parser = make_lark_parser()
        tree = parser.parse(text)
        act_result = extract_map(tree)
        self.assertEqual(exp_result, act_result)
