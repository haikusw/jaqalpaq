# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from .parameter import AnnotatedValue, ParamType
from jaqalpaq import JaqalError


class Constant(AnnotatedValue):
    """
    Bases: :class:`AnnotatedValue`

    Represents a Jaqal let statement.

    :param str name: The name to bind the constant to.
    :param value: The numeric value to bind to that name; can be either a literal value or another Constant.
    :type value: Constant, int, or float
    """

    def __init__(self, name, value):
        if isinstance(value, Constant):
            super().__init__(name, value.kind)
        elif isinstance(value, float):
            super().__init__(name, ParamType.FLOAT)
        elif isinstance(value, int):
            super().__init__(name, ParamType.INT)
        else:
            raise JaqalError(f"Invalid/non-numeric value {value} for constant {name}!")
        self._value = value

    def __repr__(self):
        return f"Constant({repr(self.name)}, {self.value})"

    def __eq__(self, other):
        try:
            return self.name == other.name and self.value == other.value
        except AttributeError:
            return False

    @property
    def value(self):
        """
        The fixed value of the constant.
        """
        return self._value

    def __int__(self):
        """Resolve this value to an integer. Raise an error if this is not an
        integer, rather than rounding."""
        if isinstance(self._value, int):
            return self._value
        else:
            raise JaqalError(f"Could not convert {type(self._value)} to int")

    def __float__(self):
        """Resolve this value converted to a float."""
        return float(self._value)

    def resolve_value(self, context=None):
        """
        Overrides: :meth:`AnnotatedValue.resolve_value`

        Unlike the superclass, ignores the context and simply returns the fixed value of
        the constant.
        """
        return self.value
