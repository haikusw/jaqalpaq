import unittest
import itertools

import jaqalpaq.core.branch
from . import common


class JaqalBranchTester(unittest.TestCase):
    """Test that a branch statement object behaves as expected."""

    def setUp(self):
        jaqalpaq.core.branch.USE_EXPERIMENTAL_BRANCH = True

    def tearDown(self):
        jaqalpaq.core.branch.USE_EXPERIMENTAL_BRANCH = False

    def test_create_branch(self):
        branch, body_count, case_statements = common.make_random_branch_statement(
            return_params=True
        )
        self.assertEqual(case_statements, branch.cases)

    def test_len(self):
        branch, body_count, case_statements = common.make_random_branch_statement(
            return_params=True
        )
        self.assertEqual(len(case_statements), len(branch))

    def test_getitem(self):
        branch, body_count, case_statements = common.make_random_branch_statement(
            return_params=True
        )
        for i in range(len(branch.cases)):
            self.assertEqual(branch[i], case_statements[i])

    def test_iterate(self):
        branch, body_count, case_statements = common.make_random_branch_statement(
            return_params=True
        )
        for exp_case, act_case in itertools.zip_longest(case_statements, branch):
            self.assertEqual(exp_case, act_case)


class JaqalCaseTester(unittest.TestCase):
    """Test that a case statement, normally an integral part of a branch
    statement, behaves as expected."""

    def test_create_case(self):
        case, state, statements = common.make_random_case(return_params=True)
        self.assertEqual(statements, case.statements)
        self.assertEqual(state, case.state)

    def test_len(self):
        case, state, statements = common.make_random_case(return_params=True)
        self.assertEqual(len(statements), len(case))

    def test_getitem(self):
        case, state, statements = common.make_random_case(return_params=True)
        for i in range(len(case.statements)):
            self.assertEqual(case[i], statements[i])

    def test_iterate(self):
        case, state, statements = common.make_random_case(return_params=True)
        for exp_stmt, act_stmt in itertools.zip_longest(statements, case):
            self.assertEqual(exp_stmt, act_stmt)
