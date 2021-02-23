# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from collections import OrderedDict

from jaqalpaq import JaqalError
from .gate import GateStatement


class AbstractGate:
    """
    The abstract base class for gate definitions. Everything here can be used whether the
    gate is defined by a macro in Jaqal, or is a gate defined by a pulse sequence in a
    gate definition file.

    :param str name: The name of the gate.
    :param parameters: What arguments (numbers, qubits, etc) the gate should be called
        with. If None, the gate takes no parameters.
    :param function ideal_unitary: A function mapping a list of all classical arguments to
        a numpy 2D array representation of the gate's ideal action in the computational
        basis.
    :type parameters: list(Parameter) or None
    """

    def __init__(self, name, parameters=None, ideal_unitary=None):
        self._name = name
        if parameters is None:
            self._parameters = []
        else:
            self._parameters = parameters
        self._ideal_unitary = ideal_unitary

    def __repr__(self):
        return f"{type(self).__name__}({self.name}, {self.parameters})"

    def __eq__(self, other):
        try:
            return self.name == other.name and self.parameters == other.parameters
        except AttributeError:
            return False

    @property
    def name(self):
        """The name of the gate."""
        return self._name

    @property
    def parameters(self):
        """
        What arguments (numbers, qubits, etc) the gate should be called with.
        """
        return self._parameters

    def call(self, *args, **kwargs):
        """
        Create a :class:`GateStatement` that calls this gate.
        The arguments to this method will be the arguments the gate is called with.
        If all arguments are keyword arguments, their names should match the names of this
        gate's parameters, and the values will be passed accordingly.
        If all arguments are positional arguments, each value will be passed to the next
        parameter in sequence.
        For convenience, calling the AbstractGate like a function is equivalent to this.

        :returns: The new statement.
        :rtype: GateStatement
        :raises JaqalError: If both keyword and positional arguments are passed.
        :raises JaqalError: If the wrong number of arguments are passed.
        :raises JaqalError: If the parameter names don't match the parameters this gate
            takes.
        """
        params = OrderedDict()
        if args and not kwargs:
            if len(args) > len(self.parameters):
                raise JaqalError(f"Too many parameters for gate {self.name}.")
            elif len(args) > len(self.parameters):
                raise JaqalError(f"Insufficient parameters for gate {self.name}.")
            else:
                for name, arg in zip([param.name for param in self.parameters], args):
                    params[name] = arg
        elif kwargs and not args:
            try:
                for param in self.parameters:
                    params[param.name] = kwargs.pop(param.name)
            except KeyError as ex:
                raise JaqalError(
                    f"Missing parameter {param.name} for gate {self.name}."
                ) from ex
            if kwargs:
                raise JaqalError(
                    f"Invalid parameters {', '.join(kwargs)} for gate {self.name}."
                )
        elif kwargs and args:
            raise JaqalError(
                "Cannot mix named and positional parameters in call to gate."
            )
        if len(self.parameters) != len(params):
            raise JaqalError(
                f"Bad argument count: expected {len(self.parameters)}, found {len(params)}"
            )
        for param in self.parameters:
            param.validate(params[param.name])
        return GateStatement(self, params)

    def __call__(self, *args, **kwargs):
        return self.call(*args, **kwargs)

    def copy(self, *, name=None, parameters=None, ideal_unitary=None):
        """Returns a shallow copy of the gate or gate definition.

        :param name: (optional) change the name in the copy.
        :param parameters: (optional) change the parameters in the copy.
        """

        kls = type(self)
        copy = kls.__new__(kls)
        copy.__dict__ = self.__dict__.copy()
        if name is not None:
            copy._name = name
        if parameters is not None:
            copy._parameters = parameters
        if ideal_unitary is not None:
            copy._ideal_unitary = ideal_unitary

        return copy


class GateDefinition(AbstractGate):
    """
    Base: :class:`AbstractGate`

    Represents a gate that's implemented by a pulse sequence in a gate definition file.
    """

    @property
    def ideal_unitary(self):
        """The ideal unitary action of the gate on its target qubits"""
        return self._ideal_unitary

    @property
    def used_qubits(self):
        """Return the parameters in this gate that are qubits. Subclasses may
        return the special symbol `all` indicating they operate on all
        qubits. Otherwise this is identical to quantum_parameters."""
        for p in self.parameters:
            try:
                if not p.classical:
                    yield p
            except JaqalError:
                # This happens if we don't have a real gate definition.
                # Lean on the upper layers being able to infer the type.
                yield p

    @property
    def quantum_parameters(self):
        """The quantum parameters (qubits or registers) this gate takes.

        :raises JaqalError: If this gate has parameters without type annotations; for
            example, if it is a macro.
        """
        try:
            return [param for param in self.parameters if not param.classical]
        except JaqalError:
            pass
        raise JaqalError("Gate {self.name} has a parameter with unknown type")

    @property
    def classical_parameters(self):
        """The classical parameters (ints or floats) this gate takes.

        :raises JaqalError: If this gate has parameters without type annotations; for
            example, if it is a macro.

        """
        try:
            return [param for param in self.parameters if param.classical]
        except JaqalError:
            pass
        raise JaqalError("Gate {self.name} has a parameter with unknown type")


class IdleGateDefinition(GateDefinition):
    """
    Base: :class:`AbstractGate`

    Represents a gate that merely idles for some duration.
    """

    # Idle gates are a scheduling mechanism.  Formally, they act on no qubits.
    _ideal_unitary = None

    def __init__(self, gate, name=None):
        # Special case handling of prepare and measure gates
        if gate.name in ("prepare_all", "measure_all"):
            raise JaqalError(f"Cannot make an idle gate for {gate.name}")
        self._parent_def = gate
        self._parameters = gate._parameters
        self._name = name if name else f"I_{gate.name}"

    @property
    def used_qubits(self):
        """Iterates over the qubits used by an idle gate: nothing.

        The idle operation does not act on any qubits.
        """
        yield from ()


class BusyGateDefinition(GateDefinition):
    """
    Base: :class:`AbstractGate`

    Represents an operation that cannot be parallelized with any other operation.
    """

    @property
    def used_qubits(self):
        yield all


def add_idle_gates(active_gates):
    """Augments a dictionary of gates with associated idle gates.

    :param active_gates: A dictionary of GateDefinition objects representing the active
      gates available.
    :return:  A list of GateDefinitions including both the active gates passed, and their
      associated idle gates.
    """
    gates = {}
    for n, g in active_gates.items():
        gates[n] = g

        try:
            g = IdleGateDefinition(g)
        except JaqalError:
            # Ignore gates that do not have corresponding idle gates
            pass
        else:
            gates[g.name] = g

    return gates
