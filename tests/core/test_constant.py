import unittest

from jaqalpaq.core.parameter import ParamType
from jaqalpaq.core.constant import Constant
from . import randomize
from . import common


class ConstantTester(unittest.TestCase):
    def test_valid_types(self):
        """Test that a Constant can only be created from valid types."""
        valid_values = [
            (randomize.random_float(), ParamType.FLOAT),
            (randomize.random_integer(), ParamType.INT),
        ]
        for value, kind in valid_values:
            const, name, _ = common.make_random_constant(
                value=value, return_params=True
            )
            self.assertEqual(kind, const.kind)
            self.assertEqual(name, const.name)

        # Note that we can also create a Constant from another Constant, but Jaqal
        # currently cannot make use of this functionality.

        reg = common.make_random_register()
        qubit = common.choose_random_qubit_getitem(reg)
        invalid_values = [None, reg, qubit]
        for value in invalid_values:
            with self.assertRaises(Exception):
                Constant(randomize.random_identifier(), value)

    def test_value(self):
        """Test that a constant yields the same value it was created with."""
        const, _, value = common.make_random_constant(return_params=True)
        common.assert_values_same(self, value, const.value)

    def test_resolve_value(self):
        """Test that constants ignore the context given in resolve_value and
        return their stored value."""
        const = common.make_random_constant()
        other_const = common.make_random_constant()
        context = {const.name: other_const.value}
        exp_value = const.value
        act_value = const.resolve_value(context)
        common.assert_values_same(self, exp_value, act_value)

    def test_classical(self):
        """Test that all constants are appropriately labeled as classical."""
        self.assertTrue(common.make_random_constant().classical)


if __name__ == "__main__":
    unittest.main()
