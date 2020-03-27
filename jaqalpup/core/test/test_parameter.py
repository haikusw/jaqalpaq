import unittest

from jaqalpup.core.parameter import (
    Parameter,
    QUBIT_TYPE, FLOAT_TYPE, REGISTER_TYPE, INT_TYPE, PARAMETER_TYPES
)
from jaqalpup.core.register import Register, NamedQubit


class ParameterTester(unittest.TestCase):

    def setUp(self):
        reg = Register('r', 17)
        self.example_values = [
            (reg, [REGISTER_TYPE, None]),
            (reg[1], [QUBIT_TYPE, None]),
            (3.14, [FLOAT_TYPE, None]),
            (1.0, [FLOAT_TYPE, INT_TYPE, None]),
            (3, [FLOAT_TYPE, INT_TYPE, None])
        ]
        self.example_params = {kind: Parameter('test', kind) for kind in PARAMETER_TYPES}

    def test_create(self):
        """Test creating a parameter with a name and kind."""
        for kind in PARAMETER_TYPES:
            name = 'test'
            param = Parameter('test', kind)
            self.assertEqual(name, param.name)
            self.assertEqual(kind, param.kind)

    def test_validate(self):
        """Test if the validate method returns True for valid values and False for
        invalid ones."""
        for ex_value, ex_types in self.example_values:
            for param_kind, param in self.example_params.items():
                if param.kind in ex_types:
                    param.validate(ex_value)
                else:
                    with self.assertRaises(Exception):
                        param.validate(ex_value)

    def test_resolve_value(self):
        """Test resolving a value within some context."""
        for param_kind, param in self.example_params.items():
            # Note: The Parameter class could, but does not, do type checking here.
            values = [value for value, value_types in self.example_values
                      if param_kind in value_types]
            for value in values:
                context = {'test': value}
                resolved_value = param.resolve_value(context)
                self.assertEqual(value, resolved_value)
                with self.assertRaises(Exception):
                    param.resolve_value()

    def test_classical(self):
        """Test that the right parameter types are classical."""
        classical_kinds = [FLOAT_TYPE, INT_TYPE]
        for param_kind, param in self.example_params.items():
            if param_kind is None:
                with self.assertRaises(Exception):
                    # Note: This behavior implies that classical checking is only reasonable when a
                    # parameter has a known type.
                    param.classical
            else:
                self.assertEqual(param_kind in classical_kinds, param.classical)

    def test_getitem(self):
        """Treat a parameter like a register or register alias."""
        allowed_kinds = [REGISTER_TYPE, None]
        for param_kind, param in self.example_params.items():
            if param_kind in allowed_kinds:
                # Note: these don't seem to have an application in Jaqal directly.
                self.assertTrue(isinstance(param[0], NamedQubit))
                self.assertTrue(isinstance(param[0:2], Register))
            else:
                with self.assertRaises(Exception):
                    param[0]
                with self.assertRaises(Exception):
                    param[0:1]
