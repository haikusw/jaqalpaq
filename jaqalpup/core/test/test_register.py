import unittest

from jaqalpup.core import Register, Constant
from .randomize import random_identifier, random_whole, random_integer


class RegisterTester(unittest.TestCase):

    # Note: We may wish to create additional Register constructors to reduce the
    # number of possible illegal ways to create a Register.

    def test_create_fundamental_fixed_size(self):
        """Test creating a fundamental register with a fixed size."""
        reg, exp_name, exp_size = self.make_random_register(return_params=True)
        self.assertEqual(exp_size, reg.size)
        self.assertEqual(exp_name, reg.name)
        self.assertTrue(reg.fundamental)
        self.assertIsNone(reg.alias_from)
        self.assertIsNone(reg.alias_slice)
        self.assertEqual(exp_size, reg.resolve_size())

    @unittest.expectedFailure
    def test_create_fundamental_unknown_size(self):
        """Test creating a fundamental register with a size determined by a let constant."""
        const, const_name, exp_size = self.make_random_size_constant(return_params=True)
        # Note: The documentation does not list Constant as an acceptable type for size.
        reg, exp_name, _ = self.make_random_register(size=const, return_params=True)
        self.assertEqual(exp_size, reg.size)
        self.assertEqual(exp_name, reg.name)
        self.assertTrue(reg.fundamental)
        self.assertIsNone(reg.alias_from)
        self.assertIsNone(reg.alias_slice)
        new_size = random_whole()
        new_const = Constant(const_name, new_size)
        self.assertEqual(exp_size, reg.resolve_size({const_name: new_const}))

    def test_fundamental_register_resolve_valid_qubit(self):
        """Test creating a fundamental register and resolving a qubit."""
        reg = self.make_random_register()
        qubit, index = self.choose_random_qubit(reg, return_params=True)
        self.assertEqual(reg, qubit.alias_from)
        self.assertEqual(index, qubit.alias_index)
        self.assertEqual(self.make_qubit_name(reg, index), qubit.name)

    def test_fundamental_register_resolve_invalid_qubit(self):
        """Test that we fail when attempting to resolve an invalid qubit from a fundamental
        register."""
        reg = self.make_random_register()
        index = random_integer(lower=reg.size, upper=reg.size + 10)
        with self.assertRaises(Exception):
            reg[index]

    @unittest.expectedFailure
    def test_fundamental_register_unknown_size_resolve_valid_qubit(self):
        """Test resolving a valid qubit from a register whose size is defined with a let constant."""
        const, const_name, exp_size = self.make_random_size_constant(return_params=True)
        # Note: The documentation does not list Constant as an acceptable type for size.
        reg, exp_name, _ = self.make_random_register(size=const, return_params=True)
        qubit, index = self.choose_random_qubit(reg, return_params=True)
        self.assertEqual(reg, qubit.alias_from)
        self.assertEqual(index, qubit.alias_index)
        self.assertEqual(self.make_qubit_name(reg, index), qubit.name)

    def test_fundamental_register_unknown_size_resolve_invalid_qubit(self):
        """Test resolving an invalid qubit from a register whole size is defined with a let constant."""
        const, const_name, exp_size = self.make_random_size_constant(return_params=True)
        # Note: The documentation does not list Constant as an acceptable type for size.
        reg, exp_name, _ = self.make_random_register(size=const, return_params=True)
        index = random_integer(lower=exp_size, upper=exp_size + 100)
        with self.assertRaises(Exception):
            reg[index]

    @unittest.expectedFailure
    def test_stretch_fundamental_register(self):
        reg, _, orig_size = self.make_random_register(return_params=True)
        self.assertEqual(orig_size, reg.size)
        reg.stretch(min(1, orig_size // 2))
        self.assertEqual(orig_size, reg.size)
        reg.stretch(orig_size)
        self.assertEqual(orig_size, reg.size)
        new_size = orig_size + 10
        reg.stretch(new_size)
        self.assertEqual(new_size, reg.size)

    @unittest.expectedFailure
    def test_stretch_fundamental_register_unknown_size(self):
        # I'm not even sure what the semantics here would be.
        self.fail()

    def test_create_map_full_register(self):
        """Test creating a map alias for an entire register."""
        reg = self.make_random_register()
        map_reg, map_name = self.make_map_full(reg, return_params=True)
        self.assertEqual(map_name, map_reg.name)
        self.assertEqual(reg.size, map_reg.size)
        self.assertEqual(reg, map_reg.alias_from)
        self.assertIsNone(map_reg.alias_slice)
        self.assertFalse(map_reg.fundamental)

    def test_create_map_slice(self):
        """Test creating a map alias for a defined slice of a register."""
        reg = self.make_random_register()
        map_reg, map_name, map_slice = self.make_map_slice(reg, return_params=True)
        self.assertEqual(map_name, map_reg.name)
        self.assertGreaterEqual(reg.size, map_reg.size)
        self.assertGreaterEqual(map_reg.size, 1)
        self.assertEqual(reg, map_reg.alias_from)
        self.assertEqual(map_slice, map_reg.alias_slice)
        self.assertFalse(map_reg.fundamental)

    @unittest.skip("This currently causes an infinite loop in resolve_size()")
    def test_create_map_slice_with_constants(self):
        """Test creating a map slice of a register using Constant values"""
        reg = self.make_random_register()
        map_slice = self.make_random_slice(reg.size)
        map_const_slice = slice(
            *[self.make_random_size_constant(value=v)
              for v in [map_slice.start, map_slice.stop, map_slice.step]]
        )
        map_reg, map_name, _ = self.make_map_slice(reg, map_slice=map_const_slice, return_params=True)
        self.assertEqual(map_name, map_reg.name)
        self.assertGreaterEqual(reg.size, map_reg.size)
        self.assertGreaterEqual(map_reg.size, 1)
        self.assertEqual(reg, map_reg.alias_from)
        self.assertEqual(map_const_slice, map_reg.alias_slice)
        self.assertFalse(map_reg.fundamental)

    @unittest.expectedFailure
    def test_full_map_resolve_qubit(self):
        reg = self.make_random_register()
        map_reg, map_name = self.make_map_full(reg, return_params=True)
        qubit, index = self.choose_random_qubit(map_reg, return_params=True)
        # Resolve directly through the map
        res_reg, res_index = map_reg.resolve_qubit(index)
        self.assertEqual(index, res_index)
        self.assertEqual(reg, res_reg)
        # Resolve through a qubit from the map
        res_reg, res_index = qubit.resolve_qubit()
        self.assertEqual(index, res_index)
        self.assertEqual(reg, res_reg)

    def test_slice_map_resolve_qubit(self):
        reg = self.make_random_register()
        map_reg, map_name, map_slice = self.make_map_slice(reg, return_params=True)
        qubit, index = self.choose_random_qubit(map_reg, return_params=True)
        # Resolve directly through the map
        res_reg, res_index = map_reg.resolve_qubit(index)
        orig_index = map_slice.start + map_slice.step * index
        self.assertEqual(orig_index, res_index)
        self.assertEqual(reg, res_reg)
        # Resolve through a qubit from the map
        res_reg, res_index = qubit.resolve_qubit()
        self.assertEqual(orig_index, res_index)
        self.assertEqual(reg, res_reg)

    @unittest.skip("Causes an infinite loop resolving qubits")
    def test_slice_map_with_constants_resolve_qubit(self):
        reg = self.make_random_register()
        map_slice = self.make_random_slice(reg.size)
        map_const_slice = slice(
            *[self.make_random_size_constant(value=v)
              for v in [map_slice.start, map_slice.stop, map_slice.step]]
        )
        map_reg, map_name, _ = self.make_map_slice(reg, map_slice=map_const_slice, return_params=True)
        qubit, index = self.choose_random_qubit(map_reg, return_params=True)
        # Resolve directly through the map
        res_reg, res_index = map_reg.resolve_qubit(index)
        orig_index = map_slice.start + map_slice.step * index
        self.assertEqual(orig_index, res_index)
        self.assertEqual(reg, res_reg)
        # Resolve through a qubit from the map
        res_reg, res_index = qubit.resolve_qubit()
        self.assertEqual(orig_index, res_index)
        self.assertEqual(reg, res_reg)

    def test_create_register_invalid_parameter(self):
        """Test creating a register in various invalid ways."""
        reg = self.make_random_register()
        with self.assertRaises(Exception):
            # No size or origin
            Register(random_identifier())
        with self.assertRaises(Exception):
            # size and slice
            Register(random_identifier(), size=random_whole(), alias_slice=self.make_random_slice())
        with self.assertRaises(Exception):
            # size and slice plus an alias register
            Register(random_identifier(), size=random_whole(), alias_from=reg, alias_slice=self.make_random_slice())
        with self.assertRaises(Exception):
            # alias register and size
            Register(random_identifier(), size=random_whole(), alias_from=reg)

    ##
    # Helper functions
    #

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
    def choose_random_qubit(reg, index=None, rand=None, return_params=False):
        if index is None:
            index = random_integer(lower=0, upper=reg.size - 1, rand=rand)
        qubit = reg[index]
        if not return_params:
            return qubit
        else:
            return qubit, index

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
