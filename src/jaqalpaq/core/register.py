# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from jaqalpaq import JaqalError
from .parameter import (
    ParamType,
    AnnotatedValue,
    Parameter,
    make_item_name,
)
from .constant import Constant


class Register:
    """
    Represents a qubit register, whether defined by a register statement or a map
    statement. Can be indexed into (but not sliced) to obtain a specific :class:`NamedQubit`
    from the register.

    :param str name: The name by which the register can be referenced.
    :param size: If the register is a fundamental register (defined by a register
        statement), specifies how many qubits are allocated for it. Must be omitted for
        non-fundamental registers.
    :type size: int or None
    :param alias_from: If the register is defined by a map statement, specifies which
        register it's mapped from all or a subset of. If omitted, the register is a
        fundamental register.
    :type alias_from: Register, Parameter, or None
    :param alias_slice: If the register isn't fundamental, specifies what subset of the
        ``alias_from`` register is mapped to this register. Can be omitted to map all of
        the register. Must be omitted for a fundamental register. Some or all of the slice
        can be specified by Parameters rather than integers.
    :type alias_slice: slice or None

    :raises JaqalError: if passed a Parameter of the wrong type.
    """

    def __init__(self, name, size=None, alias_from=None, alias_slice=None):
        self._name = name
        self._size = size
        if (alias_from is None) and not (alias_slice is None and size is not None):
            raise JaqalError(f"Invalid register declaration: {name}.")
        if (size is not None) and (alias_from is not None):
            raise JaqalError(
                f"Illegal size specification in map statement defining {name}."
            )
        self._alias_from = alias_from
        self._alias_slice = alias_slice
        if alias_slice is not None:
            if (
                isinstance(alias_slice.start, AnnotatedValue)
                or isinstance(alias_slice.stop, AnnotatedValue)
                or isinstance(alias_slice.step, AnnotatedValue)
                or isinstance(alias_from, AnnotatedValue)
            ):
                # Verify that the Parameters given have the correct types
                if isinstance(
                    alias_slice.start, AnnotatedValue
                ) and alias_slice.start.kind not in (ParamType.INT, ParamType.NONE):
                    raise JaqalError(
                        f"Cannot slice register {alias_from.name} with parameter {alias_slice.start.name} of non-integer kind {alias_slice.start.kind}."
                    )
                elif isinstance(
                    alias_slice.stop, AnnotatedValue
                ) and alias_slice.stop.kind not in (ParamType.INT, ParamType.NONE):
                    raise JaqalError(
                        f"Cannot slice register {alias_from.name} with parameter {alias_slice.stop.name} of non-integer kind {alias_slice.stop.kind}."
                    )
                elif isinstance(
                    alias_slice.step, AnnotatedValue
                ) and alias_slice.step.kind not in (ParamType.INT, ParamType.NONE):
                    raise JaqalError(
                        f"Cannot slice register {alias_from.name} with parameter {alias_slice.step.name} of non-integer kind {alias_slice.step.kind}."
                    )
                elif isinstance(alias_from, AnnotatedValue) and alias_from.kind not in (
                    ParamType.REGISTER,
                    ParamType.NONE,
                ):
                    raise JaqalError(
                        f"Cannot slice parameter {alias_from.name} of non-register kind {alias_from.kind}."
                    )
            elif alias_from.size is not None and not isinstance(
                alias_from.size, AnnotatedValue
            ):
                if alias_slice.stop > alias_from.size:
                    raise JaqalError("Index out of range.")

    def __repr__(self):
        if self.fundamental:
            return f"Register({repr(self.name)}, {self.size})"
        else:
            return f"Register({repr(self.name)}, {self.alias_from}, {self.alias_slice})"

    def __eq__(self, other):
        try:
            if self.name != other.name:
                return False
            if self.fundamental:
                return self.size == other.size
            else:
                return (
                    self.alias_from == other.alias_from
                    and self.alias_slice == other.alias_slice
                )
        except AttributeError:
            return False

    @property
    def name(self):
        """
        The name by which the register can be referenced.
        """
        return self._name

    @property
    def size(self):
        """How many qubits are in the register.

        Note: This may return a :class:`Constant` if that is how the
        size is defined. To always get an integer, use ex:
        int(reg.size).

        :raises JaqalError: If the register's size is undefined because it's mapped from
            a :class:`Parameter`.

        """
        return self.resolve_size({})

    @property
    def fundamental(self):
        """
        True if the register is defined by a register statement, False if it's mapped from
        some other register.
        """
        return self.alias_from is None

    @property
    def alias_from(self):
        """
        What register this register's mapped from, or None if it's fundamental.
        """
        return self._alias_from

    @property
    def alias_slice(self):
        """
        If the register isn't fundamental, specifies what subset of the
        ``alias_from`` register is mapped to this register. None if this register is
        fundamental or if all of ``alias_from`` is mapped to it.
        """
        return self._alias_slice

    def resolve_size(self, context=None):
        """
        Determines how many qubits are in the register.

        :param dict context: The context that's used to resolve any :class:`AnnotatedValue`
            needed to actually fix the register's size.
        :returns: The size of the register.
        :rtype: int
        """

        if self._size is not None:
            return self._size

        context = context or {}

        alias_from = self.alias_from
        while isinstance(alias_from, AnnotatedValue):
            alias_from.resolve_value(context)
        if self.alias_slice is None:
            return self.alias_from.size

        start = self.alias_slice.start or 0
        step = self.alias_slice.step
        if step is None:
            step = 1
        stop = self.alias_slice.stop

        def resolve_annotated_value(value):
            while isinstance(value, AnnotatedValue):
                value = value.resolve_value(context)
            return value

        start = resolve_annotated_value(start)
        step = resolve_annotated_value(step)
        stop = resolve_annotated_value(stop)

        return len(range(start, stop, step))

    def resolve_qubit(self, idx, context=None):
        """
        Given a specific qubit in this register, follow all map statements back to find
        which fundamental register, and which qubit in that register, the specified qubit
        is equivalent to.

        :param int idx: Which qubit from this register to resolve.
        :param dict context: The context that's used to resolve any :class:`AnnotatedValue`
            needed to actually fix the referenced qubit.
        :returns: The fundamental register, and what index into that register, the specified qubit corresponds to.
        :rtype: (Register, int)
        """

        context = context or {}

        if self.size is not None and idx >= self.size:
            raise JaqalError("Index out of range.")
        if self.fundamental:
            return (self, idx)
        alias_from = self.alias_from
        if self.alias_slice is None:
            return alias_from.resolve_qubit(idx, context)
        start = self.alias_slice.start or 0
        step = self.alias_slice.step
        if step is None:
            step = 1

        def resolve_annotated_value(value):
            while isinstance(value, AnnotatedValue):
                value = value.resolve_value(context)
            return value

        start = resolve_annotated_value(start)
        step = resolve_annotated_value(step)

        return alias_from.resolve_qubit(start + idx * step, context)

    def __getitem__(self, key):
        name = make_item_name(self, key)
        if isinstance(key, slice):
            raise JaqalError(
                "Anonymous slices are not currently supported; slice only in a map statement."
            )
            # But if the backend ever supports it, just replace the above line with the below line:
            # return Register(self.name + '[' + str(key) + ']', alias_from=self, alias_slice=key)
        else:
            return NamedQubit(name, self, key)

    def __len__(self):
        return self.size

    def __iter__(self):
        for key in range(self.size):
            yield self[key]


class NamedQubit:
    """
    Represents a single qubit, which has had a name associated with it, typically by a map
    statement.

    :param str name: The name by which the qubit can be referenced.
    :param alias_from: Specifies which register this qubit is taken from.
    :type alias_from: Register, Parameter
    :param alias_index: Specifies which qubit in the ``alias_from`` register this qubit
        actually represents.
    :type alias_index: int, Parameter

    :raises JaqalError: If the index is an int larger than the the size of the source register.
    """

    def __init__(self, name, alias_from, alias_index):
        self._name = name
        self._alias_from = alias_from
        self._alias_index = alias_index
        if alias_index is None or alias_from is None:
            raise JaqalError(f"Invalid map statement constructing qubit {name}.")
        if isinstance(alias_index, AnnotatedValue) or isinstance(
            alias_from, AnnotatedValue
        ):
            if isinstance(alias_index, AnnotatedValue) and alias_index.kind not in (
                ParamType.INT,
                ParamType.NONE,
            ):
                raise JaqalError(
                    f"Cannot slice register {alias_from.name} with parameter {alias_index.name} of non-integer kind {alias_index.kind}."
                )
            if isinstance(alias_from, AnnotatedValue) and alias_from.kind not in (
                ParamType.REGISTER,
                ParamType.NONE,
            ):
                raise JaqalError(
                    f"Cannot slice parameter {alias_from.name} of non-register kind {alias_from.kind}."
                )
        else:
            try:
                from_size = int(alias_from.size)
            except JaqalError:
                return
            if alias_index >= from_size:
                raise JaqalError("Index out of range.")

    def __repr__(self):
        return f"NamedQubit({self.name}, {self.alias_from}, {self.alias_index})"

    def __eq__(self, other):
        try:
            # Note: With map aliases it's actually non-trivial to know if this qubit is the same as another.
            # So this heuristic is good enough for unit testing, but if this were ever used in the main logic
            # things might break down.
            return (
                self.name == other.name
                and self.alias_from.name == other.alias_from.name
                and self.alias_index == other.alias_index
            )
        except AttributeError:
            return False

    @property
    def name(self):
        """
        The name by which the qubit can be referenced.
        """
        return self._name

    @property
    def fundamental(self):
        """
        Always false, because single qubits cannot be defined with register statements.
        """
        return False

    @property
    def alias_from(self):
        """
        Specifies which register this qubit is taken from.
        """
        return self._alias_from

    @property
    def alias_index(self):
        """
        Specifies which qubit in the ``alias_from`` register this qubit actually represents.
        """
        return self._alias_index

    def resolve_qubit(self, context=None):
        """
        Follow all map statements back to find which fundamental register, and which qubit
        in that register, this qubit is equivalent to.

        :param dict context: The context that's used to resolve any :class:`AnnotatedValue`
            needed to actually fix the referenced qubit.
        :returns: The fundamental register, and what index into that register, this qubit corresponds to.
        :rtype: (Register, int)
        """
        context = context or {}
        alias_index = self.alias_index
        alias_from = self.alias_from
        while isinstance(alias_index, AnnotatedValue):
            alias_index = alias_index.resolve_value(context)
        while isinstance(alias_from, AnnotatedValue):
            alias_from = alias_from.resolve_value(context)
        return alias_from.resolve_qubit(alias_index, context)

    def renamed(self, name):
        """
        Creates a copy of this qubit with a different name.

        :param str name: The name to give the new qubit.
        :returns: A new qubit with the same referent as this one but a different name.
        :rtype: NamedQubit
        """
        return NamedQubit(name, self.alias_from, self.alias_index)
