# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from importlib import import_module

from jaqalpaq import JaqalError


class UsePulsesStatement:
    """
    Represents a Jaqal from . usepulses statement.

    :param str module: the . delineated module path
    :param list[str] names: either the special value `all`, or a list of tokens to import
    """

    def __init__(self, module, names):
        self._module = module

        if names is all or names == "*":
            self._names = all
        else:
            self._names = tuple(names)

    def __repr__(self):
        if self._names is all:
            return f"UsePulsesStatement('{str(self._module)}', '*')"
        else:
            names = ", ".join(repr(name) for name in self._names)
            return f"UsePulsesStatement('{str(self._module)}', [{names}])"

    def __eq__(self, other):
        try:
            return self._module == other._module and self._names == other._names
        except AttributeError:
            return False

    @property
    def module(self):
        """
        The name of the module calling to be imported
        """
        return self._module

    @property
    def names(self):
        """
        The names to import from the module
        """
        return self._names

    def load_pulses(self):
        module = import_module(str(self._module))
        native_gates = module.NATIVE_GATES

        if self._names is all:
            return native_gates

        # Todo: filter the native gates based on self._names
        raise JaqalError("Only from ... usepulses * currently supported.")

    def __hash__(self):
        return hash((self.__class__, self._module, self._names))
