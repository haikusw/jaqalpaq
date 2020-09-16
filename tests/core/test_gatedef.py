import unittest

from .abstractgate import AbstractGateTesterBase
from . import common
from jaqalpaq.core import GateDefinition


class GateDefinitionTester(AbstractGateTesterBase, unittest.TestCase):
    def create_random_instance(self, **kwargs):
        return common.make_random_gate_definition(**kwargs)

    @property
    def tested_type(self):
        return GateDefinition
