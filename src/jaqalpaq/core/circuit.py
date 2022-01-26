# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from .block import BlockStatement, LoopStatement
from .constant import Constant
from .gate import GateStatement
from .gatedef import GateDefinition
from .macro import Macro
from .register import Register, NamedQubit
from .identifier import is_identifier_valid
from jaqalpaq.error import JaqalError
from jaqalpaq.utilities import RESERVED_WORDS
import re


class Circuit:
    """
    An immutable representation of an entire Jaqal program. The `constants`, `registers`,
    and `native_gates` properties correspond to the statements of the Jaqal program's
    header; the `macros` and `body` properties correspond to the body statements of the
    Jaqal program.

    This initializer should rarely be called directly; instead, the
    :class:`jaqalpaq.core.CircuitBuilder` object-oriented interface or
    :func:`jaqalpaq.core.build` S-expression-based interface should be used to construct
    circuit objects.

    :param native_gates: Set these gates as the native gates to be used in this circuit.
        If not given, gate definitions are automatically generated.
    :type native_gates: Optional[dict] or Optional[list]
    :raises JaqalError: If `native_gates` is a dict and any gate's name doesn't match its
        dictionary key.
    :raises JaqalError: If any of the `native_gates` aren't :class:`GateDefinition`.  For
        example, if a macro is passed as a native gate.

    """

    def __init__(self, native_gates=None):
        self._constants = {}
        self._macros = {}
        self._registers = {}
        self._native_gates = normalize_native_gates(native_gates)
        self._body = BlockStatement()
        self._usepulses = []

    def __repr__(self):
        return f"Circuit(usepulses={self._usepulses}, constants={self._constants}, macros={self._macros}, native_gates={self._native_gates}, registers={self._registers}, body={self._body})"

    def __eq__(self, other):
        try:
            return (
                self.constants == other.constants
                and self.macros == other.macros
                and self.native_gates == other.native_gates
                and self.registers == other.registers
                and self.body == other.body
                and self.usepulses == self.usepulses
            )
        except AttributeError:
            return False

    @property
    def constants(self):
        """Read-only access to a dictionary mapping names to :class:`Constant` objects,
        corresponding to ``let`` statements in the header of a Jaqal file."""
        return self._constants

    @property
    def macros(self):
        """Read-only access to a dictionary mapping names to :class:`Macro` objects,
        corresponding to ``macro`` statements in a Jaqal file."""
        return self._macros

    @property
    def native_gates(self):
        """Read-only access to a dictionary mapping names to :class:`GateDefinition`
        objects, corresponding to the contents of a gate definition file."""
        return self._native_gates

    @property
    def registers(self):
        """Read-only access to a dictionary mapping names to :class:`Register`
        objects, corresponding to ``register`` and ``map`` statements in the header of a Jaqal
        file."""
        return self._registers

    @property
    def body(self):
        """Read-only access to a :class:`BlockStatement` object that contains the main body of
        the program."""
        return self._body

    @property
    def usepulses(self):
        """Read-only access to a list of :class:`UsePulsesStatement` objects,
        corresponding to ``from ? usepulses ?`` statements in a Jaqal file."""
        return self._usepulses

    def fundamental_registers(self):
        """
        :returns: all of the circuit's registers that correspond to ``register`` statements, that is, all those that are not aliases for some other register.
        :rtype: list(Register)
        """
        return [r for r in self.registers.values() if r.fundamental]


def normalize_native_gates(native_gates):
    """Takes in the different ways that native gates can be represented and
    returns a dictionary.

    :param native_gates: A list or dict of gates, or None.
    :type native_gates: Optional[dict] or Optional[list]
    """
    native_gates = native_gates or {}
    if not isinstance(native_gates, dict):
        # This covers all iterables like list and tuple
        native_gates = {gate.name: gate for gate in native_gates}
    if any(name != gate.name for name, gate in native_gates.items()):
        raise JaqalError("Native gate dictionary key did not match its name")
    if any(not isinstance(gate, GateDefinition) for gate in native_gates.values()):
        raise JaqalError("Native gates must be GateDefinition instances")
    return native_gates
