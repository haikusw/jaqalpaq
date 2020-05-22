from collections import OrderedDict

from jaqal import JaqalError
from .gate import GateStatement


class AbstractGate:
    """
    The abstract base class for gate definitions. Everything here can be used whether the gate is defined by a macro in Jaqal, or is a gate defined by a pulse sequence in a gate definition file.

    :param str name: The name of the gate.
    :param parameters: What arguments (numbers, qubits, etc) the gate should be called with. If None, the gate takes no parameters.
    :type parameters: list(Parameter) or None
    """

    def __init__(self, name, parameters=None, ideal_action=None):
        self._name = name
        if parameters is None:
            self._parameters = []
        else:
            self._parameters = parameters
        self._ideal_action = ideal_action

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
    def ideal_action(self):
        """
        Returns the ideal unitary action of the gate.
        """
        return self._ideal_action

    def ideal_action_pygsti(self, parms):
        """
        Returns the ideal unitary action of the gate.

        Is compatible with pygsti's build_from_parameterization
        nonstd_gate_unitaries parameters.
        """
        if parms:
            return self._ideal_action(*parms)
        else:
            import numpy

            return numpy.identity(2 ** self.quantum_parameters)

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
                raise JaqalError("Too many parameters for gate %s." % self.name)
            elif len(args) > len(self.parameters):
                raise JaqalError("Insufficient parameters for gate %s." % self.name)
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
