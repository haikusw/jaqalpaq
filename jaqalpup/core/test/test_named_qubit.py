import unittest

from jaqalpup.core.test.randomize import random_identifier, random_whole, random_integer
from jaqalpup.core.test.common import CommonBase


class NamedQubitTester(unittest.TestCase, CommonBase):

    def test_create_directly_with_register(self):
        """Create a named qubit using its constructor from a register."""
        reg = self.make_random_register()
        qubit, name, index = self.choose_random_qubit_init(reg, return_params=True)
        self.assertEqual(name, qubit.name)
        self.assertEqual(reg, qubit.alias_from)
        self.assertEqual(index, qubit.alias_index)
        # Not sure where the following field would be used
        self.assertFalse(qubit.fundamental)

    def test_resolve_qubit(self):
        """Test resolving a qubit back to its register."""
        reg = self.make_random_register()
        qubit, name, index = self.choose_random_qubit_init(reg, return_params=True)
        res_reg, res_index = qubit.resolve_qubit()
        self.assertEqual(reg, res_reg)
        self.assertEqual(index, res_index)

    def test_create_from_map(self):
        """Create a named qubit with an alias as its register."""
        reg = self.make_random_register()
        map_reg = self.make_map_full(reg)
        qubit, name, index = self.choose_random_qubit_init(map_reg, return_params=True)
        self.assertEqual(name, qubit.name)
        self.assertEqual(map_reg, qubit.alias_from)
        self.assertEqual(index, qubit.alias_index)
        # Not sure where the following field would be used
        self.assertFalse(qubit.fundamental)

    @unittest.expectedFailure
    def test_resolve_from_map(self):
        """Resolve a named qubit created from a map."""
        reg = self.make_random_register()
        map_reg = self.make_map_full(reg)
        qubit, name, index = self.choose_random_qubit_init(map_reg, return_params=True)
        res_reg, res_index = qubit.resolve_qubit()
        self.assertEqual(reg, res_reg)
        self.assertEqual(index, res_index)

    def test_create_from_map_slice(self):
        """Test creating a named qubit from a map that is a register slice."""
        reg = self.make_random_register()
        map_reg, map_name, map_slice = self.make_map_slice(reg, return_params=True)
        qubit, name, index = self.choose_random_qubit_init(map_reg, return_params=True)
        self.assertEqual(name, qubit.name)
        self.assertEqual(map_reg, qubit.alias_from)
        self.assertEqual(index, qubit.alias_index)
        # Not sure where the following field would be used
        self.assertFalse(qubit.fundamental)

    def test_resolve_from_map_slice(self):
        """Test resolving a named qubit created from a register slice."""
        reg = self.make_random_register()
        map_reg, map_name, map_slice = self.make_map_slice(reg, return_params=True)
        qubit, name, index = self.choose_random_qubit_init(map_reg, return_params=True)
        orig_index = map_slice.start + map_slice.step * index
        res_reg, res_index = qubit.resolve_qubit()
        self.assertEqual(reg, res_reg)
        self.assertEqual(orig_index, res_index)

    @unittest.skip("Infinite loop in NamedQubit.__init__")
    def test_create_from_map_slice_with_constants(self):
        """Test creating a new qubit from a map slice defined with constants."""
        reg = self.make_random_register()
        map_slice = self.make_random_slice(reg.size)
        map_const_slice = slice(
            *[self.make_random_size_constant(value=v)
              for v in [map_slice.start, map_slice.stop, map_slice.step]]
        )
        map_reg, map_name, _ = self.make_map_slice(reg, map_slice=map_const_slice, return_params=True)
        # We make our own integer because there is temporarily a bug that hangs when we
        # automatically do it because reg.size has an infinite loop.
        index = random_integer(lower=0, upper=len(range(map_slice.start, map_slice.stop, map_slice.step)))
        qubit, name, _ = self.choose_random_qubit_init(map_reg, index=index, return_params=True)
        self.assertEqual(name, qubit.name)
        self.assertEqual(map_reg, qubit.alias_from)
        self.assertEqual(index, qubit.alias_index)
        # Not sure where the following field would be used
        self.assertFalse(qubit.fundamental)

    @unittest.skip("Infinite loop in NamedQubit.__init__")
    def test_resolve_from_map_slice_with_constants(self):
        """Test resolving a qubit from a map slice defined with constants."""
        reg = self.make_random_register()
        map_slice = self.make_random_slice(reg.size)
        map_const_slice = slice(
            *[self.make_random_size_constant(value=v)
              for v in [map_slice.start, map_slice.stop, map_slice.step]]
        )
        map_reg, map_name, _ = self.make_map_slice(reg, map_slice=map_const_slice, return_params=True)
        # We make our own integer because there is temporarily a bug that hangs when we
        # automatically do it because reg.size has an infinite loop.
        index = random_integer(lower=0, upper=len(range(map_slice.start, map_slice.stop, map_slice.step)))
        qubit, name, _ = self.choose_random_qubit_init(map_reg, index=index, return_params=True)
        orig_index = map_slice.start + map_slice.step * index
        res_reg, res_index = qubit.resolve_qubit()
        self.assertEqual(reg, res_reg)
        self.assertEqual(orig_index, res_index)

    def test_renamed(self):
        """Test creating a new named qubit with a different name."""
        reg = self.make_random_register()
        qubit, name, index = self.choose_random_qubit_init(reg, return_params=True)
        new_name = random_identifier()
        renamed_qubit = qubit.renamed(new_name)
        self.assertEqual(new_name, renamed_qubit.name)
        self.assertEqual(qubit.alias_from, renamed_qubit.alias_from)
        self.assertEqual(qubit.alias_index, renamed_qubit.alias_index)
        self.assertFalse(renamed_qubit.fundamental)
