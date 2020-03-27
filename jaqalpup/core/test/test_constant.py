import unittest
import random

from jaqalpup.core.parameter import (
    QUBIT_TYPE, FLOAT_TYPE, REGISTER_TYPE, INT_TYPE, PARAMETER_TYPES
)
from jaqalpup.core.constant import Constant
from jaqalpup.core.register import Register


class ConstantTester(unittest.TestCase):
    def test_valid_types(self):
        """Test that a Constant can only be created from valid types."""
        valid_values = [
            (3.14, FLOAT_TYPE),
            (42, INT_TYPE)
        ]
        for value, kind in valid_values:
            const = Constant('test', value)
            self.assertEqual(kind, const.kind)
            self.assertEqual('test', const.name)

        # Note that we can also create a Constant from another Constant, but Jaqal
        # currently cannot make use of this functionality.

        reg = Register('r', 17)
        qubit = reg[2]
        invalid_values = [
            None,
            reg,
            qubit
        ]
        for value in invalid_values:
            with self.assertRaises(Exception):
                Constant('test', value)

    def test_value(self):
        """Test that a constant yields the same value it was created with."""
        for value in self.get_random_valid_values():
            self.assertEqual(value, Constant('test', value).value)

    def test_resolve_value(self):
        """Test that constants ignore the context given in resolve_value and
        return their stored value."""
        for value, other_value in zip(self.get_random_valid_values(), self.get_random_valid_values()):
            const = Constant('test', value)
            context = {'test': other_value}
            self.assertEqual(value, const.resolve_value(context))

    def test_classical(self):
        """Test that all constants are appropriately labeled as classical."""
        for value in self.get_random_valid_values():
            self.assertTrue(Constant('test', value))

    ##
    # Helper methods
    #

    def get_random_valid_values(self):
        """Return a list of values that are valid to use for constants. These values
        will represent all valid value types."""
        float_values = [random.uniform(-10, 10) for _ in range(10)]
        int_values = [random.randint(-10, 10) for _ in range(10)]
        values = float_values + int_values
        return values

if __name__ == '__main__':
    unittest.main()
