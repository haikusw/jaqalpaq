# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.

from contextlib import contextmanager
import importlib
import functools
from typing import Any
from inspect import getfullargspec

from jaqalpaq.error import JaqalError
from jaqalpaq.core.circuitbuilder import build
from jaqalpaq.run import run_jaqal_circuit
from jaqalpaq.generator import generate_jaqal_program


def circuit(
    *args,
    inject_pulses=None,
    autoload_pulses="ignore",
    **kwargs,
):
    """Inner decorator function defining a Jaqal circuit by adding all
    statements defined inside of the function decorated with this
    decorator.

    :param inject_pulses: If given, use these pulses specifically.

    :param autoload_pulses: Whether to use the usepulses statement
    when parsing. Can be given the special value "ignore" (default) to
    use import pulses when possible, but continue in the case of
    failure.

    :rtype: QCircuit

    """

    def outer(func):
        @functools.wraps(func)
        def inner(*args, **kwargs):
            stack = Stack()
            qsyntax = Q(stack)
            with stack.frame():
                func(qsyntax, *args, **kwargs)
                return circuit_from_stack(
                    qsyntax,
                    inject_pulses=inject_pulses,
                    autoload_pulses=autoload_pulses,
                )

        argspec = getfullargspec(func)
        default_count = len(argspec.defaults) if argspec.defaults else 0
        return mark_qcircuit(inner, len(argspec.args) - default_count - 1)

    if len(args) > 0 and callable(args[0]):
        return outer(args[0])
    else:
        return outer


class Q:
    """A local namespace for instructions that the user issues to create a
    Jaqal circuit. The framework creates this and automatically passes
    it as the first argument of a user-defined circuit.

    """

    def __init__(self, stack):
        self._stack = stack

    def __getattr__(self, name):
        """Return an object that represents a gate wiith an unknown
        definition.

        :param string name: The name of the gate
        """

        return QGate(name, self._stack)

    def register(self, size, name=None):
        """Create a register with the given size.

        :param size: The number of qubits in the register.
        :type size: int or QConstant
        :rtype: QRegister
        """

        reg = QRegister(size, name=name)
        self._stack.set_register(reg)
        return reg

    def let(self, value, name=None):
        """Define a constant in Jaqal. This isn't strictly necessary, but can
        have some benefits such as allowing the hardware to override this
        value.

        :param value: The value that this constant will always be equal to.
        :type value: int, float, or QConstant
        :rtype: QConstant
        """

        let = QConstant(value, name=name)
        self._stack.set_let(let)
        return let

    @contextmanager
    def loop(self, repeats):
        with self._stack.frame():
            yield
            loop = QLoop.from_stack(self._stack, argument=repeats)

        self._stack.set_statement(loop)

    @contextmanager
    def sequential(self):
        with self._stack.frame():
            yield
            block = QSequentialBlock.from_stack(self._stack)
        self._stack.set_statement(block)

    @contextmanager
    def parallel(self):
        with self._stack.frame():
            yield
            block = QParallelBlock.from_stack(self._stack)
        self._stack.set_statement(block)

    @contextmanager
    def subcircuit(self, argument=1):
        with self._stack.frame():
            yield
            block = QSubcircuitBlock.from_stack(self._stack, argument=argument)
        self._stack.set_statement(block)

    def usepulses(self, module, names="*"):
        """Instruct the Jaqal file to import its pulses from the given
        file."""

        usepulses = QUsePulses(module, names)
        self._stack.set_usepulses(usepulses)
        return usepulses

    @contextmanager
    def branch(self):
        with self._stack.frame():
            yield
            block = QBranch.from_stack(self._stack)
        self._stack.set_statement(block)

    @contextmanager
    def case(self, label):
        with self._stack.frame():
            yield
            block = QCase.from_stack(self._stack, argument=label)
        self._stack.set_statement(block)

    @property
    def registers(self):
        """Return a list of all registers registered so far."""
        return list(self._stack.iter_registers())

    @property
    def lets(self):
        """Return a list of all let constants registered so far."""
        return list(self._stack.iter_lets())


class QRegister:
    def __init__(self, size, name=None):
        self.size = self._validate_normalize_size(size)
        self.name = name

    @staticmethod
    def _validate_normalize_size(size):
        return validate_int(size)

    def __getitem__(self, index):
        # Note: we could check if index is a slice, and create a
        # register alias object. If the slice parameters are all
        # integers, we can do the mapping in this module, but if any
        # of them are let constants, we would have to resort to a map
        # statement. Otherwise, let overrides would not work properly.
        return QNamedQubit(self, index)


class QNamedQubit:
    def __init__(self, source, index):
        self.source = self._validate_source(source)
        self.index = self._validate_normalize_index(index)

    @staticmethod
    def _validate_source(source):
        if not isinstance(source, QRegister):
            # The user should not be able to trigger this error
            raise JaqalError(f"Cannot create named qubit with source {source}")
        return source

    @staticmethod
    def _validate_normalize_index(index):
        return validate_int(index)


class QConstant:
    def __init__(self, value, name=None):
        self.value = self._validate_normalize_constant(value)
        self.name = name

    @staticmethod
    def _validate_normalize_constant(value):
        # Resolve all values down to an integer or floating point
        # number. As a convenience to the user, we will allow them to
        # give us a constant, even though base Jaqal does/did not
        # allow this.
        if isinstance(value, QConstant):
            value = QConstant.value
        if not isinstance(value, (int, float)):
            raise JaqalError(f"Invalid let value {value}")
        return value


def circuit_from_stack(
    qsyntax,
    inject_pulses=None,
    autoload_pulses="ignore",
    prepare="prepare_all",
    measure="measure_all",
):
    """Construct a new QCircuit using the elements that have been pushed
    on the stack."""
    if qsyntax._stack.depth() > 1:
        raise JaqalError("Q stack corrupted: too many stack frames.")

    let_names = [let.name for let in qsyntax.lets]
    register_names = [reg.name for reg in qsyntax.registers]
    namer = Namer(let_names=let_names, register_names=register_names)
    sexpr = ["circuit"]

    imports = {}
    for usepulses in qsyntax._stack.iter_usepulses():
        imports[usepulses.module] = usepulses.names
        sexpr.append(["usepulses", usepulses.module, usepulses.names])

    # TODO: Make sure our generated let and register names don't
    # conflict with user-provided ones

    let_dict = {}
    for let in qsyntax._stack.iter_lets():
        name = namer.name_let(let)
        let_dict[let] = name
        sexpr.append(["let", name, let.value])

    # Gate objects for preparing and measuring all
    # qubits. Measurement and prepartion of a limited number of
    # qubits are treated like any other gate.
    prepare_gate = QGateCall(prepare, ())
    measure_gate = QGateCall(measure, ())

    def lookup_object(obj):
        if isinstance(obj, QConstant):
            return let_dict[obj]
        if isinstance(obj, QRegister):
            return register_dict[obj]
        if isinstance(obj, QNamedQubit):
            return [
                "array_item",
                lookup_object(obj.source),
                lookup_object(obj.index),
            ]

        return obj

    register_dict = {}
    for reg in qsyntax._stack.iter_registers():
        name = namer.name_register(reg)
        register_dict[reg] = name
        sexpr.append(["register", name, lookup_object(reg.size)])

    statements = list(qsyntax._stack.iter_statements())

    do_implicit_measure = len(statements) == 0 or not statements[0].starts_with_prepare(
        prepare
    )

    if do_implicit_measure:
        sexpr.append(prepare_gate.build(lookup_object))

    # Process all statements and fill in their arguments
    for stmt in statements:
        sexpr.append(stmt.build(lookup_object))

    if do_implicit_measure:
        sexpr.append(measure_gate.build(lookup_object))

    # If the user has not given us gates and has provided at least
    # one usepulses statement, and we can import that module, do
    # so when creating the circuit.
    if (
        autoload_pulses
        and inject_pulses is None
        and len(list(qsyntax._stack.iter_usepulses())) > 0
    ):
        for module in imports:
            try:
                importlib.import_module(module)
            except Exception:
                if autoload_pulses != "ignore":
                    raise JaqalError(f"Could not load pulses from `{module}'")
                else:
                    autoload_pulses = False
                    break

    if autoload_pulses == "ignore":
        # We can get here if either inject_pulses was given or all
        # modules could be imported. If there are no usepulses,
        # then we would not have engaged the above logic, and we
        # must set autoload_pulses to False or we will get an
        # error if the user attempts to use any gate.
        autoload_pulses = len(list(qsyntax._stack.iter_usepulses())) > 0

    if not isinstance(autoload_pulses, bool):
        # build() expects autoload_pulses to be Boolean, so we
        # ensure we've filtered out any special values by now.
        raise JaqalError(f"Bad value for autoload_pulses: {autoload_pulses}")

    return build(sexpr, inject_pulses=inject_pulses, autoload_pulses=autoload_pulses)


class QGate:
    """A gate without specific arguments that define it precisely."""

    def __init__(self, name, stack):
        self.name = name
        self._stack = stack

    def __call__(self, *args):
        # We do pretty late binding here, that way the user can create
        # a QGate object, bind it to a name in Python, then call it
        # multiple times with different arguments and create a
        # different gate each time.
        self._stack.set_statement(QGateCall(self.name, args))


class QGateCall:
    """A specific instantiation of a gate with arguments."""

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def build(self, lookup_object):
        """Using a builder object, add a gate with this gate's name and
        arguments. The arguments may need to be looked up with
        lookup_object."""
        return ["gate", self.name, *(lookup_object(arg) for arg in self.args)]

    def starts_with_prepare(self, name):
        return self.name == name


class QBlock:
    """A Jaqal block, either sequential, parallel, or a subcircuit. This
    is meant to be subclassed, although except for internal_name it has
    defaults that work for some of its subclasses."""

    # The name used by the circuit builder for a given block
    internal_name: str = ""

    # The number of arguments this block takes.
    arity: int = 0

    # If the user gives no argument, fill in this. A value of None
    # here indicates it is required.
    default_argument: Any = None

    # Some blocks are actually constructs containing a sequential
    # block as far as the circuit builder back end is
    # concerned. Accommodate them by setting this to True.
    wrap_statements = False

    @classmethod
    def from_stack(cls, stack, argument=None):
        statements = list(stack.iter_statements())
        return cls(statements, argument=argument)

    def __init__(self, statements, argument=None):
        assert self.internal_name != "", "QBlock must be subclassed"
        self.statements = statements
        self.argument = argument

    def build(self, lookup_object):
        ret = []

        ret.append(self.internal_name)

        assert self.arity in (0, 1), "Internal block arity badly implemented"
        if self.arity == 1:
            if self.argument is None:
                if self.default_argument is None:
                    raise JaqalError(f"{type(self).__name__} requires an argument")
                ret.append(self.default_argument)
            ret.append(lookup_object(self.argument))

        if self.wrap_statements:
            inner = [QSequentialBlock.internal_name]
            ret.append(inner)
        else:
            inner = ret

        for stmt in self.statements:
            self._validate_statement(stmt)
            inner.append(stmt.build(lookup_object))

        return ret

    def _validate_statement(self, statement):
        """Make sure a statement can exist inside this block given our white
        and blacklists."""

        # We only check blocks. There are cases (e.g. inside a branch
        # block) where non-blocks are not allowed, but we don't check
        # that here. We could, but I want to keep this logic from
        # getting too complicated as any checking here is really just
        # a courtesy to the user.
        if isinstance(statement, QBlock):
            if not self._validate_inner_block(statement):
                raise JaqalError(
                    f"{type(self).__name__}: cannot contain block {type(statement).__name__}"
                )

    def _validate_inner_block(self, blk):
        """Determine if a block can nest into this. Override this default
        action if needed."""
        return not isinstance(blk, QCase)

    def starts_with_prepare(self, name):
        return len(self.statements) > 0 and self.statements[0].starts_with_prepare(name)


class QSequentialBlock(QBlock):
    internal_name = "sequential_block"


class QParallelBlock(QBlock):
    internal_name = "parallel_block"


class QSubcircuitBlock(QBlock):
    internal_name = "subcircuit_block"
    arity = 1
    default_argument = 1

    def _validate_inner_block(self, blk):
        return not isinstance(blk, (QCase, QSubcircuitBlock))

    def starts_with_prepare(self, _name):
        return True


class QLoop(QBlock):
    internal_name = "loop"
    arity = 1
    wrap_statements = True


class QBranch(QBlock):
    internal_name = "branch"

    def _validate_inner_block(self, blk):
        return isinstance(blk, QCase)


class QCase(QBlock):
    internal_name = "case"
    arity = 1
    wrap_statements = True


class QUsePulses:
    @classmethod
    def __init__(self, module, names):
        self.module = module
        self.names = self._validate_normalize_names(names)

    @staticmethod
    def _validate_normalize_names(names):
        """Make sure the names imported are valid. For now, only importing all
        identifiers into the global namespace is supported, so names must be
        "*" or the special symbol `all'."""

        if names == all or names == "*":
            return "*"

        raise JaqalError(f"usepulses names must be '*' or all")


#
# Private implementation details
#


class Stack:
    """Implement a stack of where Jaqal objects are stored. Each frame
    corresponds to a new block."""

    def __init__(self):
        self.stack = []
        self.top_context = {
            "lets": [],
            "registers": [],
            "usepulses": [],
        }

    def set_let(self, item):
        self.top_context["lets"].append(item)

    def set_register(self, item):
        self.top_context["registers"].append(item)

    def set_statement(self, item):
        if self.depth() == 0:
            raise JaqalError("Cannot define statements outside a circuit")
        self.stack[-1].append(item)

    def set_usepulses(self, item):
        self.top_context["usepulses"].append(item)

    def iter_lets(self):
        return iter(self.top_context["lets"])

    def iter_registers(self):
        return iter(self.top_context["registers"])

    def iter_usepulses(self):
        return iter(self.top_context["usepulses"])

    def iter_statements(self):
        return iter(self.stack[-1])

    def push(self):
        self.stack.append([])

    def pop(self):
        if self.depth() == 0:
            raise JaqalError("Popping frame off empty stack")
        self.stack.pop()

    def depth(self):
        return len(self.stack)

    @contextmanager
    def frame(self):
        start_depth = self.depth()

        self.push()

        try:
            yield
        finally:
            self.pop()

        if start_depth != self.depth():
            raise JaqalError("Stack depth changed in block")


class Namer:
    """Internal class for assigning names to anonymous objects.

    Names are chosen by incrementing an index in a template. The
    template is chosen so as to be short, but unlikely to be chosen by
    a user. If the user chooses such a name anyway, we will be careful
    to avoid using it.

    """

    register_template = "__r{}"
    let_template = "__c{}"

    def __init__(self, *, let_names, register_names):
        self.let_names = let_names
        self.register_names = register_names
        self.next_let = 0
        self.next_register = 0

    def name_let(self, let):
        assert isinstance(let, QConstant)
        if let.name is not None:
            return let.name
        name, self.next_let = self._choose_name(
            self.let_template, self.next_let, self.let_names
        )
        return name

    def name_register(self, register):
        assert isinstance(register, QRegister)
        if register.name is not None:
            return register.name
        name, self.next_register = self._choose_name(
            self.register_template, self.next_register, self.register_names
        )
        return name

    def _choose_name(self, template, index, user_names):
        """Choose a new name for some object. Return the name chosen and the
        new value for the index. Avoids choosing any name in user_names."""

        while True:
            name = template.format(index)
            index += 1
            if name not in user_names:
                break
        return name, index


def validate_int(value):
    """Make sure this value is an int or a Constant that is an int."""
    if isinstance(value, QConstant):
        pre_value = value.value
        post_value = int(value.value)
    else:
        pre_value = value
        post_value = int(value)
    if pre_value != post_value:
        raise JaqalError(f"Invalid int value {value}")
    return value


def mark_qcircuit(func, argcount):
    """Internally-used function to help identify circuits by introspection
    tools."""
    func._QCIRCUIT_FUNCTION = True
    func._QCIRCUIT_ARG_COUNT = argcount
    return func


def is_qcircuit(func, argcount=None):
    """Return whether the given function is properly annotated Q circuit
    that when called will return a QCircuit object. If argcount is not
    None, also check whether it accepts the given number of arguments.

    """

    if not callable(func):
        return False
    if not hasattr(func, "_QCIRCUIT_FUNCTION"):
        return False
    if argcount is not None and getattr(func, "_QCIRCUIT_ARG_COUNT") != argcount:
        return False
    return True
