import unittest


from .abstractgate import AbstractGateTesterBase
from . import common
from jaqalpaq.core import Macro


class JaqalPaqMacroTester(AbstractGateTesterBase, unittest.TestCase):
    def create_random_instance(self, **kwargs):
        return common.make_random_macro_definition(**kwargs)

    @property
    def tested_type(self):
        return Macro

    def test_make_macro(self):
        """Test creating a macro and checking its parameters. The base class
        will already do part of this test but will not check parameters."""
        macro, body = self.create_random_instance(return_body=True)
        self.assertEqual(body, macro.body)
