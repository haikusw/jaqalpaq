# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from jaqalpaq.error import JaqalError


class UsePulsesStatement:
    """
    Represents a Jaqal from . usepulses statement.

    :param str module: the . delineated module path
    :param list[str] names: either the special value `all`, or a list of tokens to import
    """

    _gates = None

    def __init__(self, module, names, *, filename=None):
        self._module = module
        self._filename = filename

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
        # Deprecated
        try:
            self._gates
        except AttributeError:
            self.load()

        native_gates = {}
        self.update_gates(native_gates)
        return native_gates

    def update_gates(self, gates, inject_pulses=False):
        if not self._gates:
            self._load()

        if self._names is not all:
            # Todo: filter the native gates based on self._names
            raise JaqalError("Only from ... usepulses * currently supported.")

        for g in self._gates.values():
            # inject_pulses overrides usepulses
            if inject_pulses and g.name in inject_pulses:
                continue

            # but later usepulses override earlier imports
            gates[g.name] = g

    def _load(self):
        from jaqalpaq._import import get_jaqal_gates

        self._gates = get_jaqal_gates(self._module, jaqal_filename=self._filename)

    def __hash__(self):
        return hash((self.__class__, self._module, self._names))
