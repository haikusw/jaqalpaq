from collections import OrderedDict

from jaqalpaq import JaqalError
from .gate import GateStatement


class AbstractGate:
    """
    The abstract base class for gate definitions. Everything here can be used whether the gate is defined by a macro in Jaqal, or is a gate defined by a pulse sequence in a gate definition file.

    :param str name: The name of the gate.
    :param parameters: What arguments (numbers, qubits, etc) the gate should be called with. If None, the gate takes no parameters.
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
        """
        The name of the gate.
        """
        return self._name

    @property
    def parameters(self):
        """
        What arguments (numbers, qubits, etc) the gate should be called with.
        """
        return self._parameters

    @property
    def ideal_unitary(self):
        """
        Returns the ideal unitary action of the gate on its target qubits.

        Takes as parameters all classical arguments.
        """
        return self._ideal_unitary

    def ideal_unitary_pygsti(self, parms):
        """
        Returns the ideal unitary action of the gate on its target qubits.

        Takes as a parameter: a list of all classical arguments.

        Is compatible with pygsti's build_from_parameterization
        nonstd_gate_unitaries parameters.
        """
        if parms:
            return self._ideal_unitary(*parms)
        else:
            import numpy

            return numpy.identity(2 ** self.quantum_parameters)

    @property
    def used_qubits(self):
        for p in self._parameters:
            try:
                if not p.classical:
                    yield p
            except JaqalError:
                # This happens if we don't have a real gate definition.
                # Lean on the upper layers being able to infer the type.
                yield p

    @property
    def quantum_parameters(self):
        try:
            return self._quantum_parameters
        except AttributeError:
            self.count_parameters()
            return self._quantum_parameters

    @property
    def classical_parameters(self):
        try:
            return self._classical_parameters
        except AttributeError:
            self.count_parameters()
            return self._classical_parameters

    def count_parameters(self):
        c = 0
        q = 0
        for p in self._parameters:
            if p.classical:
                c += 1
            else:
                q += 1

        self._classical_parameters = c
        self._quantum_parameters = q

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
        :raises JaqalError: If the parameter names don't match the parameters this gate takes.
        """
        params = OrderedDict()
        if args and not kwargs:
            if len(args) > len(self.parameters):
                raise JaqalError(f"Too many parameters for gate {self.name}.")
            elif len(args) > len(self.parameters):
                raise JaqalError("Insufficient parameters for gate {self.name}.")
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


class GateDefinition(AbstractGate):
    """
    Base: :class:`AbstractGate`

    Represents a gate that's implemented by a pulse sequence in a gate definition file.
    """

    pass


class IdleGateDefinition(GateDefinition):
    """
    Base: :class:`AbstractGate`

    Represents a gate that merely idles for some duration.
    """

    def __init__(self, gate, name=None):
        self._parent_def = gate
        self._parameters = gate._parameters
        self._name = name if name else f"I_{gate.name}"

    @property
    def _ideal_unitary(self):
        parent = self._parent_def
        if parent._ideal_unitary:
            import numpy

            return lambda: numpy.identity(2 ** parent.quantum_parameters)
        else:
            return None

    @property
    def used_qubits(self):
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
    gates = []
    for g in active_gates:
        gates.append(g)

        # Special case handling of preparation and measurement
        if g.name not in ("prepare_all", "measure_all"):
            gates.append(IdleGateDefinition(g))

    return tuple(gates)
