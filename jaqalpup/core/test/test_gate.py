import unittest

from jaqalpup.core import GateStatement

from jaqalpup.core.test.randomize import random_identifier, random_whole
from jaqalpup.core.test.common import CommonBase


class GateTester(unittest.TestCase, CommonBase):

    def test_create_gate_no_parameters(self):
        """Test creating a gate without parameters."""
        name = random_identifier()
        gate = GateStatement(name)
        self.assertEqual(name, gate.name)
        self.assertEqual({}, gate.parameters)

    def test_create_gate_with_parameters(self):
        """Test creating a gate with parameters."""
        # Note: this tests with the GateStatement's __init__ method. The normal method
        # of creating a gate is from a GateDefinition, which we'll test in the GateDefinition
        # testing suite.
        name = random_identifier()
        param_count = random_whole()
        parameters = {param_name: param for param, param_name, _
                      in (self.make_random_parameter(return_params=True) for _ in range(param_count))}
        gate = GateStatement(name, parameters)
        self.assertEqual(name, gate.name)
        self.assertEqual(parameters, gate.parameters)
