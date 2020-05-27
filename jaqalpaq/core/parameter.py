from jaqalpaq import JaqalError

QUBIT_TYPE = "qubit"
FLOAT_TYPE = "float"
REGISTER_TYPE = "register"
INT_TYPE = "int"
PARAMETER_TYPES = (QUBIT_TYPE, FLOAT_TYPE, REGISTER_TYPE, INT_TYPE, None)


class AnnotatedValue:
    """
    An abstract base class that represents a named (and optionally type-annotated) value.
    The actual value it represents may be context-dependent, but the name and type
    annotation are not.
    Currently, it's used to implement both gate parameters and let statements, though it
    may find other uses as the language evolves.

    :param str name: The name the AnnotatedValue is labeled with.
    :param kind: Optionally, an annotation denoting the the type of the value as
        :data:`jaqalpaq.core.QUBIT_TYPE`, :data:`jaqalpaq.core.FLOAT_TYPE`,
        :data:`jaqalpaq.core.REGISTER_TYPE`, or :data:`jaqalpaq.core.INT_TYPE`.
        If None, can hold a value of any type (like a macro parameter).
    """

    def __init__(self, name, kind):
        self._name = name
        if kind not in PARAMETER_TYPES:
            raise JaqalError("Invalid parameter type specifier %s." % kind)
        self._kind = kind

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

    def resolve_value(self, context={}):
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
        if self.name in context:
            return context[self.name]
        else:
            raise JaqalError("Unbound identifier %s." % self.name)

    @property
    def classical(self):
        if self._kind is None:
            raise JaqalError(f"No type defined for parameter {self.name}.")
        return self._kind not in (QUBIT_TYPE, REGISTER_TYPE)


class Parameter(AnnotatedValue):
    """
    Base: :class:`AnnotatedValue`

    Represents a parameter that a gate or macro accepts. In addition to the functionality
    of the base class, it also supports type-checking. Furthermore, it can be indexed and
    sliced, if it represents a :class:`Register` parameter. Thus, it can be used within
    the body of a macro exactly as if it were a register defined by a ``map`` or ``reg``
    statement.
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

        if self.kind == QUBIT_TYPE:
            if isinstance(value, NamedQubit):
                pass
            elif isinstance(value, AnnotatedValue) and value.kind in (QUBIT_TYPE, None):
                pass
            else:
                raise JaqalError(
                    "Type-checking failed: parameter %s=%s does not have type %s."
                    % (str(self.name), str(value), str(self.kind))
                )
        elif self.kind == REGISTER_TYPE:
            if isinstance(value, Register):
                pass
            elif isinstance(value, AnnotatedValue) and value.kind in (
                REGISTER_TYPE,
                None,
            ):
                pass
            else:
                raise JaqalError(
                    "Type-checking failed: parameter %s=%s does not have type %s."
                    % (str(self.name), str(value), str(self.kind))
                )
        elif self.kind == FLOAT_TYPE:
            if isinstance(value, float) or isinstance(value, int):
                pass
            elif isinstance(value, AnnotatedValue) and value.kind in (
                INT_TYPE,
                FLOAT_TYPE,
                None,
            ):
                pass
            else:
                raise JaqalError(
                    "Type-checking failed: parameter %s=%s does not have type %s."
                    % (str(self.name), str(value), str(self.kind))
                )
        elif self.kind == INT_TYPE:
            if (isinstance(value, float) and int(value) == value) or isinstance(
                value, int
            ):
                pass
            elif isinstance(value, AnnotatedValue) and value.kind in (INT_TYPE, None):
                pass
            else:
                raise JaqalError(
                    "Type-checking failed: parameter %s=%s does not have type %s."
                    % (str(self.name), str(value), str(self.kind))
                )
        elif self.kind == None:
            # A parameter with kind None can take anything as input.
            # Such parameters are normally from user-defined macros, where there's no
            # ability to add type annotations in the Jaqal.
            pass
        else:
            raise JaqalError(
                "Type-checking failed: unknown parameter type %s." + str(self.kind)
            )

    def __getitem__(self, key):
        # Only makes sense for register parameters, but we'll let Register and NamedQubit do the typechecking.
        from .register import Register, NamedQubit

        if isinstance(key, slice):
            return Register(
                self.name + "[" + str(key) + "]", alias_from=self, alias_slice=key
            )
        else:
            return NamedQubit(self.name + "[" + str(key) + "]", self, key)
