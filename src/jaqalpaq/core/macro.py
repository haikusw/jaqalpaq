# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from .block import BlockStatement
from .gatedef import AbstractGate


class Macro(AbstractGate):
    """
    Base: :class:`AbstractGate`

    Represents a gate that's implemented by Jaqal macro statement.

    :param str name: The name of the gate.
    :param parameters: What arguments (numbers, qubits, etc) the gate should be called with. If None, the gate takes no parameters.
    :type parameters: list(Parameter) or None
    :param body: The implementation of the macro. If None, an empty sequential BlockStatement is created.
    :type body: BlockStatement or None
    """

    def __init__(self, name, parameters=None, body=None):
        super().__init__(name, parameters)
        if body is None:
            self._body = BlockStatement()
        else:
            self._body = body

    def __repr__(self):
        return f"Macro({repr(self.name)}, {self.parameters}, {self.body})"

    def __eq__(self, other):
        return (
            self.name == other.name
            and self.parameters == other.parameters
            and self.body == other.body
        )

    @property
    def body(self):
        """
        A :class:`BlockStatement` that implements the macro.
        """
        return self._body
