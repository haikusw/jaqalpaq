import unittest

from jaqalpup.core.test.abstractgate import AbstractGateTesterBase
import jaqalpup.core.test.common as common
from jaqalpup.core import GateDefinition


class GateDefinitionTester(AbstractGateTesterBase, unittest.TestCase):

    def create_random_instance(self, **kwargs):
        return common.make_random_gate_definition(**kwargs)

    @property
    def tested_type(self):
        return GateDefinition