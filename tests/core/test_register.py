import unittest

from jaqalpaq.core import Register, Constant
from .randomize import random_identifier, random_whole, random_integer
from . import common


class RegisterTester(unittest.TestCase):

    # Note: We may wish to create additional Register constructors to reduce the
    # number of possible illegal ways to create a Register.

    def test_create_fundamental_fixed_size(self):
        """Test creating a fundamental register with a fixed size."""
        reg, exp_name, exp_size = common.make_random_register(return_params=True)
        self.assertEqual(exp_size, reg.size)
        self.assertEqual(exp_name, reg.name)
        self.assertTrue(reg.fundamental)
        self.assertIsNone(reg.alias_from)
        self.assertIsNone(reg.alias_slice)
        self.assertEqual(exp_size, reg.resolve_size())

    def test_create_fundamental_unknown_size(self):
        """Test creating a fundamental register with a size determined by a let constant."""
        const, const_name, exp_size = common.make_random_size_constant(
            return_params=True
        )
        reg, exp_name, _ = common.make_random_register(size=const, return_params=True)
        self.assertEqual(exp_size, int(reg.size))
        self.assertEqual(exp_name, reg.name)
        self.assertTrue(reg.fundamental)
        self.assertIsNone(reg.alias_from)
        self.assertIsNone(reg.alias_slice)
        new_size = random_whole()
        new_const = Constant(const_name, new_size)
        self.assertEqual(exp_size, int(reg.resolve_size({const_name: new_const})))

    def test_fundamental_register_resolve_valid_qubit(self):
        """Test creating a fundamental register and resolving a qubit."""
        reg = common.make_random_register()
        qubit, index = common.choose_random_qubit_getitem(reg, return_params=True)
        self.assertEqual(reg, qubit.alias_from)
        self.assertEqual(index, qubit.alias_index)
        self.assertEqual(common.make_qubit_name(reg, index), qubit.name)

    def test_fundamental_register_resolve_invalid_qubit(self):
        """Test that we fail when attempting to resolve an invalid qubit from a fundamental
        register."""
        reg = common.make_random_register()
        index = random_integer(lower=reg.size, upper=reg.size + 10)
        with self.assertRaises(Exception):
            reg[index]

    def test_fundamental_register_unknown_size_resolve_valid_qubit(self):
        """Test resolving a valid qubit from a register whose size is defined with a let constant."""
        const, const_name, exp_size = common.make_random_size_constant(
            return_params=True
        )
        reg, exp_name, _ = common.make_random_register(size=const, return_params=True)
        qubit, index = common.choose_random_qubit_getitem(reg, return_params=True)
        self.assertEqual(reg, qubit.alias_from)
        self.assertEqual(index, qubit.alias_index)
        self.assertEqual(common.make_qubit_name(reg, index), qubit.name)

    def test_fundamental_register_unknown_size_resolve_invalid_qubit(self):
        """Test resolving an invalid qubit from a register whole size is defined with a let constant."""
        const, const_name, exp_size = common.make_random_size_constant(
            return_params=True
        )
        reg, exp_name, _ = common.make_random_register(size=const, return_params=True)
        index = random_integer(lower=exp_size, upper=exp_size + 100)
        with self.assertRaises(Exception):
            reg[index]

    def test_create_map_full_register(self):
        """Test creating a map alias for an entire register."""
        reg = common.make_random_register()
        map_reg, map_name = common.make_map_full(reg, return_params=True)
        self.assertEqual(map_name, map_reg.name)
        self.assertEqual(reg.size, map_reg.size)
        self.assertEqual(reg, map_reg.alias_from)
        self.assertIsNone(map_reg.alias_slice)
        self.assertFalse(map_reg.fundamental)

    def test_create_map_slice(self):
        """Test creating a map alias for a defined slice of a register."""
        reg = common.make_random_register()
        map_reg, map_name, map_slice = common.make_map_slice(reg, return_params=True)
        self.assertEqual(map_name, map_reg.name)
        self.assertGreaterEqual(reg.size, map_reg.size)
        self.assertGreaterEqual(map_reg.size, 1)
        self.assertEqual(reg, map_reg.alias_from)
        self.assertEqual(map_slice, map_reg.alias_slice)
        self.assertFalse(map_reg.fundamental)

    def test_create_map_slice_with_constants(self):
        """Test creating a map slice of a register using Constant values"""
        reg = common.make_random_register()
        map_slice = common.make_random_slice(reg.size)
        map_const_slice = slice(
            *[
                common.make_random_size_constant(value=v)
                for v in [map_slice.start, map_slice.stop, map_slice.step]
            ]
        )
        map_reg, map_name, _ = common.make_map_slice(
            reg, map_slice=map_const_slice, return_params=True
        )
        self.assertEqual(map_name, map_reg.name)
        self.assertGreaterEqual(reg.size, map_reg.size)
        self.assertGreaterEqual(map_reg.size, 1)
        self.assertEqual(reg, map_reg.alias_from)
        self.assertEqual(map_const_slice, map_reg.alias_slice)
        self.assertFalse(map_reg.fundamental)

    def test_full_map_resolve_qubit(self):
        reg = common.make_random_register()
        map_reg, map_name = common.make_map_full(reg, return_params=True)
        qubit, index = common.choose_random_qubit_getitem(map_reg, return_params=True)
        # Resolve directly through the map
        res_reg, res_index = map_reg.resolve_qubit(index)
        self.assertEqual(index, res_index)
        self.assertEqual(reg, res_reg)
        # Resolve through a qubit from the map
        res_reg, res_index = qubit.resolve_qubit()
        self.assertEqual(index, res_index)
        self.assertEqual(reg, res_reg)

    def test_slice_map_resolve_qubit(self):
        reg = common.make_random_register()
        map_reg, map_name, map_slice = common.make_map_slice(reg, return_params=True)
        qubit, index = common.choose_random_qubit_getitem(map_reg, return_params=True)
        # Resolve directly through the map
        res_reg, res_index = map_reg.resolve_qubit(index)
        orig_index = map_slice.start + map_slice.step * index
        self.assertEqual(orig_index, res_index)
        self.assertEqual(reg, res_reg)
        # Resolve through a qubit from the map
        res_reg, res_index = qubit.resolve_qubit()
        self.assertEqual(orig_index, res_index)
        self.assertEqual(reg, res_reg)

    def test_slice_map_with_constants_resolve_qubit(self):
        reg = common.make_random_register()
        map_slice = common.make_random_slice(reg.size)
        map_const_slice = slice(
            *[
                common.make_random_size_constant(value=v)
                for v in [map_slice.start, map_slice.stop, map_slice.step]
            ]
        )
        map_reg, map_name, _ = common.make_map_slice(
            reg, map_slice=map_const_slice, return_params=True
        )
        qubit, index = common.choose_random_qubit_getitem(map_reg, return_params=True)
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
        reg = common.make_random_register()
        with self.assertRaises(Exception):
            # No size or origin
            Register(random_identifier())
        with self.assertRaises(Exception):
            # size and slice
            Register(
                random_identifier(),
                size=random_whole(),
                alias_slice=common.make_random_slice(reg.size),
            )
        with self.assertRaises(Exception):
            # size and slice plus an alias register
            Register(
                random_identifier(),
                size=random_whole(),
                alias_from=reg,
                alias_slice=common.make_random_slice(reg.size),
            )
        with self.assertRaises(Exception):
            # alias register and size
            Register(random_identifier(), size=random_whole(), alias_from=reg)
