import random

from jaqalpup.core import (
    Register, Constant, NamedQubit, PARAMETER_TYPES, Parameter, QUBIT_TYPE, FLOAT_TYPE,
    REGISTER_TYPE, INT_TYPE
)
from .randomize import (
    random_identifier, random_whole, random_integer, random_float, resolve_random_instance
)


class CommonBase:
    """Testing functions common to various core type tests."""

    @classmethod
    def make_random_parameter(cls, allowed_types=None, rand=None, return_params=False):
        """Return a parameter with a random type and name."""
        rand = resolve_random_instance(rand)
        name = random_identifier(rand=rand)
        if allowed_types is None:
            allowed_types = PARAMETER_TYPES
        param_type = rand.choice(allowed_types)
        if param_type not in PARAMETER_TYPES:
            raise ValueError(f"Unknown parameter type {param_type}")
        param = Parameter(name, param_type)
        if not return_params:
            return param
        else:
            return param, name, param_type

    @staticmethod
    def make_random_register(name=None, size=None, rand=None, return_params=False):
        """Make a random register"""
        if name is None:
            name = random_identifier(rand=rand)
        if size is None:
            size = random_whole(rand=rand)
        reg = Register(name, size)
        if not return_params:
            return reg
        else:
            return reg, name, size

    @staticmethod
    def make_random_size_constant(name=None, value=None, rand=None, return_params=False):
        """Make a random Constant that can represent a size"""
        if name is None:
            name = random_identifier(rand=rand)
        if value is None:
            value = random_whole(rand=rand)
        const = Constant(name, value)
        if not return_params:
            return const
        else:
            return const, name, value

    @staticmethod
    def choose_random_qubit_getitem(reg, index=None, rand=None, return_params=False):
        """Choose a random qubit from a register with its getitem special method."""
        if index is None:
            index = random_integer(lower=0, upper=reg.size - 1, rand=rand)
        qubit = reg[index]
        if not return_params:
            return qubit
        else:
            return qubit, index

    @staticmethod
    def choose_random_qubit_init(reg, name=None, index=None, rand=None, return_params=False):
        """Choose a random qubit from a register using the NamedQubit's constructor."""
        if index is None:
            index = random_integer(lower=0, upper=reg.size - 1, rand=rand)
        if name is None:
            name = random_identifier(rand=rand)
        qubit = NamedQubit(name, reg, index)
        if not return_params:
            return qubit
        else:
            return qubit, name, index

    @staticmethod
    def make_qubit_name(reg, index):
        return f"{reg.name}[{index}]"

    @staticmethod
    def make_map_full(reg, name=None, rand=None, return_params=False):
        """Make a map alias to the given register."""
        if name is None:
            name = random_identifier(rand=rand)
        map_reg = Register(name, alias_from=reg)
        if not return_params:
            return map_reg
        else:
            return map_reg, name

    @classmethod
    def make_map_slice(cls, reg, name=None, map_slice=None, rand=None, return_params=False):
        """Make a map alias to a slice of the given register."""
        if name is None:
            name = random_identifier(rand=rand)
        if map_slice is None:
            map_slice = cls.make_random_slice(reg.size, rand=rand)
        map_reg = Register(name, alias_from=reg, alias_slice=map_slice)
        if not return_params:
            return map_reg
        else:
            return map_reg, name, map_slice

    @staticmethod
    def make_random_slice(upper, rand=None):
        """Return a slice of an array with upper bound upper. Guaranteed to have
        at least one element."""
        start = random_whole(upper=upper - 1, rand=rand)
        length = random_whole(upper=(upper - start), rand=rand)
        step = random_whole(upper=16, rand=rand)
        return slice(start, start + length, step)
