import unittest
import random

from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.error import JaqalError


class JaqalVisitorTester(unittest.TestCase):
    def test_visit_type(self):
        class Foo:
            def __init__(self, x):
                self.x = x

        class TestVisitor(Visitor):
            def visit_Foo(self, obj):
                return obj.x

        exp_value = random.uniform(-100, 100)
        foo = Foo(exp_value)
        visitor = TestVisitor()
        act_value = visitor.visit_Foo(foo)
        self.assertEqual(exp_value, act_value)

    def test_visit_super_type(self):
        class Foo:
            def __init__(self, x):
                self.x = x

        class Bar(Foo):
            pass

        class TestVisitor(Visitor):
            def visit_Foo(self, obj):
                return obj.x

        exp_value = random.uniform(-100, 100)
        foo = Bar(exp_value)
        visitor = TestVisitor()
        act_value = visitor.visit_Foo(foo)
        self.assertEqual(exp_value, act_value)

    def test_unknown_class(self):
        class TestVisitor(Visitor):
            def visit_Foo(self, obj):
                return obj.x

        visitor = TestVisitor()
        with self.assertRaises(JaqalError):
            visitor.visit(1)
