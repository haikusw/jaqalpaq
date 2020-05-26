import unittest

from jaqalpaq.core import GateStatement

from .randomize import random_identifier, random_whole
from . import common


class GateTester(unittest.TestCase):
    def test_create_gate_no_parameters(self):
        """Test creating a gate without parameters."""
        gate, definition, _ = common.make_random_gate_statement(
            count=0, return_params=True
        )
        self.assertEqual(definition.name, gate.name)
        self.assertEqual({}, gate.parameters)

    def test_create_gate_with_parameters(self):
        """Test creating a gate with parameters."""
        count = random_whole()
        gate, definition, arguments = common.make_random_gate_statement(
            count=count, return_params=True
        )
        self.assertEqual(definition.name, gate.name)
        self.assertEqual(arguments, gate.parameters)
