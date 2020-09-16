# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import enum

from jaqalpaq import JaqalError


class ParamMeta(enum.EnumMeta):
    @property
    def types(cls):
        """A list of all the types in this enumeration. This just excludes
        NONE."""
        return [typ for typ in cls if typ != cls.NONE]


class ParamType(enum.Enum, metaclass=ParamMeta):
    NONE = None  # Unknown type
    QUBIT = enum.auto()
    FLOAT = enum.auto()
    REGISTER = enum.auto()
    INT = enum.auto()

    @classmethod
    def make(cls, obj):
        """Create a new ParamType or raise a JaqalError if not possible."""
        try:
            return cls(obj)
        except ValueError:
            pass
        raise JaqalError(f"{obj} is not convertible to ParamType")


class AnnotatedValue:
    """
    An abstract base class that represents a named (and optionally type-annotated) value.
    The actual value it represents may be context-dependent, but the name and type
    annotation are not.
    Currently, it's used to implement both gate parameters and let statements, though it
    may find other uses as the language evolves.

    :param str name: The name the AnnotatedValue is labeled with.
    :param kind: Optionally, an annotation denoting the the type of the value. If None, can hold a value of any type (like a macro parameter).
    """

    def __init__(self, name, kind):
        self._name = name
        self._kind = ParamType.make(kind)

    def __repr__(self):
        return f"Parameter({repr(self.name)}, {self.kind})"

    def __eq__(self, other):
        try:
            return self.name == other.name and self.kind == other.kind
        except AttributeError:
            return False

    @property
    def name(self):
        """
        The name the AnnotatedValue is labeled with.
        """
        return self._name

    @property
    def kind(self):
        """
        Optionally, an annotation denoting the type of the value.
        """
        return self._kind

    def resolve_value(self, context=None):
        """
        Determines what value the AnnotatedValue represents in a particular context. For
        example, a gate parameter may have different values each time the gate is called.
        The implementation provided here simply checks to see if the name of this
        AnnotatedValue is defined in the context, and if so returns its value. However,
        subclasses are likely to provide different behavior.

        :param dict context: A dictionary mapping names defined in the scope of interest
            to the values corresponding to those names.

        :returns: What value the AnnotatedValue represents.
        :raises JaqalError: If the AnnotatedValue doesn't represent a fixed value within
            the context specified.
        """
        if context and self.name in context:
            return context[self.name]
        else:
            raise JaqalError(f"Unbound identifier {self.name}.")

    @property
    def classical(self):
        """
        A boolean flag denoting whether this AnnotatedValue has a classical type
        (`ParamType.INT` or `ParamType.FLOAT`) or a quantum type (`ParamType.QUBIT` or
        `ParamType.REGISTER`).

        :raises JaqalError: If the AnnotatedValue doesn't have a type annotation.
        """

        if self._kind == ParamType.NONE:
            raise JaqalError(f"No type defined for parameter {self.name}.")
        return self._kind not in (ParamType.QUBIT, ParamType.REGISTER)


class Parameter(AnnotatedValue):
    """
    Base: :class:`AnnotatedValue`

    Represents a parameter that a gate or macro accepts. In addition to the functionality
    of the base class, it also supports type-checking. Furthermore, it can be indexed and
    sliced, if it represents a :class:`Register` parameter. Thus, it can be used within
    the body of a macro exactly as if it were a register defined by a ``map`` or
    ``register`` statement.
    """

    def validate(self, value):
        """
        Checks to see if the given value can be passed to this Parameter.
        Specifically, the value's type is checked against any type annotation this
        Parameter may have.

        :param value: The candidate value to validate.
        :raises JaqalError: If the value is not acceptable for this Parameter.
        """
        from .register import NamedQubit, Register

        if self.kind == ParamType.QUBIT:
            if isinstance(value, NamedQubit):
                pass
            elif isinstance(value, AnnotatedValue) and value.kind in (
                ParamType.QUBIT,
                ParamType.NONE,
            ):
                pass
            else:
                raise JaqalError(
                    f"Type-checking failed: parameter {self.name}={value} does not have type {self.kind}."
                )
        elif self.kind == ParamType.REGISTER:
            if isinstance(value, Register):
                pass
            elif isinstance(value, AnnotatedValue) and value.kind in (
                ParamType.REGISTER,
                ParamType.NONE,
            ):
                pass
            else:
                raise JaqalError(
                    f"Type-checking failed: parameter {self.name}={value} does not have type {self.kind}."
                )
        elif self.kind == ParamType.FLOAT:
            if isinstance(value, float) or isinstance(value, int):
                pass
            elif isinstance(value, AnnotatedValue) and value.kind in (
                ParamType.INT,
                ParamType.FLOAT,
                ParamType.NONE,
            ):
                pass
            else:
                raise JaqalError(
                    f"Type-checking failed: parameter {self.name}={value} does not have type {self.kind}."
                )
        elif self.kind == ParamType.INT:
            if (isinstance(value, float) and int(value) == value) or isinstance(
                value, int
            ):
                pass
            elif isinstance(value, AnnotatedValue) and value.kind in (
                ParamType.INT,
                ParamType.NONE,
            ):
                pass
            else:
                raise JaqalError(
                    f"Type-checking failed: parameter {self.name}={value} does not have type {self.kind}."
                )
        elif self.kind == ParamType.NONE:
            # A parameter with kind None can take anything as input.
            # Such parameters are normally from user-defined macros, where there's no
            # ability to add type annotations in the Jaqal.
            pass
        else:
            raise JaqalError(
                f"Type-checking failed: unknown parameter type {self.kind}."
            )

    def __getitem__(self, key):
        # Only makes sense for register parameters, but we'll let Register and NamedQubit do the typechecking.
        from .register import Register, NamedQubit

        name = make_item_name(self, key)
        if isinstance(key, slice):
            return Register(name, alias_from=self, alias_slice=key)
        else:
            return NamedQubit(name, self, key)


def make_item_name(array, index):
    """Create a name from an indexable object and its index."""
    return f"{array.name}[{index}]"
