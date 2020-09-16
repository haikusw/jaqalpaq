import unittest
import itertools

from . import common
from .randomize import random_whole, random_integer


class JaqalBlockTester(unittest.TestCase):
    def test_create_sequential_block(self):
        """Test creating a sequential block."""
        block, statements = common.make_random_block(return_params=True)
        self.assertEqual(statements, block.statements)
        self.assertFalse(block.parallel)

    def test_create_parallel_block(self):
        """Test creating a parallel block."""
        block, statements = common.make_random_block(parallel=True, return_params=True)
        self.assertEqual(statements, block.statements)
        self.assertTrue(block.parallel)

    def test_len(self):
        # Note: I don't think we need this
        block = common.make_random_block()
        self.assertEqual(len(block.statements), len(block))

    def test_iterate(self):
        # Note: I don't think we need this
        block = common.make_random_block()
        for exp_stmt, act_stmt in itertools.zip_longest(block.statements, block):
            self.assertEqual(exp_stmt, act_stmt, f"{exp_stmt} != {act_stmt}")

    def test_getitem(self):
        # Note: I don't think we need this
        block = common.make_random_block()
        for i in range(len(block.statements)):
            self.assertEqual(block.statements[i], block[i])
