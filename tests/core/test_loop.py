import unittest
import itertools

from . import common
from .randomize import random_whole, random_integer


class JaqalLoopTester(unittest.TestCase):
    def test_create_loop(self):
        """Test creating a loop."""
        # Note: The LoopStatement could do validity checking for its arguments, but doesn't.
        loop, iterations, statements = common.make_random_loop_statement(
            return_params=True
        )
        self.assertEqual(iterations, loop.iterations)
        self.assertEqual(statements, loop.statements)

    def test_len(self):
        # Note: I don't think we need this
        loop = common.make_random_loop_statement()
        self.assertEqual(len(loop.statements), len(loop))

    def test_iterate(self):
        # Note: I don't think we need this
        loop = common.make_random_loop_statement()
        for exp_stmt, act_stmt in itertools.zip_longest(loop.statements, loop):
            self.assertEqual(exp_stmt, act_stmt, f"{exp_stmt} != {act_stmt}")

    def test_getitem(self):
        # Note: I don't think we need this
        loop = common.make_random_loop_statement()
        for i in range(len(loop.statements)):
            self.assertEqual(loop.statements[i], loop[i])
