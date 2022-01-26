# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from typing import Dict
from contextlib import contextmanager

from .constant import Constant
from .macro import Macro
from .register import Register, NamedQubit
from .gate import GateStatement
from .gatedef import GateDefinition, AbstractGate
from .circuit import Circuit, normalize_native_gates
from .parameter import Parameter
from .block import BlockStatement, LoopStatement, UnscheduledBlockStatement
from .branch import BranchStatement, CaseStatement
from .algorithm.visitor import Visitor
from .usepulses import UsePulsesStatement

from jaqalpaq.error import JaqalError


def build(expression, inject_pulses=None, autoload_pulses=False, filename=None):
    """Given an expression in a specific format, return the appropriate type, recursively
    constructed, from the core types library.

    :param expression: A tuple or list acting like an S-expression. Also accepts core
        types and just returns them.
    :param inject_pulses: If given, use these pulses specifically.
    :param bool autoload_pulses: Whether to employ the usepulses statement for parsing.
        Requires appropriate gate definitions.
    :param str filename: The effective location of the Jaqal file, used for relative
        imports.

    :return: An appropriate core type object.
    :raises JaqalError: If an undefined identifier is used.
    :raises JaqalError: If an s-expression not of the following forms is given.
    :raises JaqalError: If the same name is defined twice.

    Each expression must be an s-expression where the first element defines the type and
    the rest of the elements define the arguments. The signatures are as follows where
    the first element is before the colon and the remaining are space separated after the
    colon.

    circuit : \*elements
    macro : \*parameter_names block
    let : identifier value
    register : name size
    map : name [src_name | src_name src_index | src_name src_start src_stop src_step]
    loop : count sequential_block
    gate : \*arguments
    sequential_block : \*statements
    parallel_block : \*statements
    subcircuit_block : \*statements
    array_item : identifier index
    usepulses : identifier [all]

    In lieu of an s-expression, the appropriate type from the core library will also be
    accepted. This allows the user to build up new expressions using partially built old
    ones.

    Note: jaqalpaq partially supports qualified namespaces in identifiers. This function
    assumes all identifiers are one string, that is they are multiple legal identifiers
    joined by periods.

    """

    builder = Builder(
        inject_pulses=inject_pulses, autoload_pulses=autoload_pulses, filename=filename
    )
    return builder.build(expression)


##
# Private classes and functions. Use the build() function.
#


class Builder:
    """Helper class to recursively build a circuit (or type within it) from s-expressions."""

    def __init__(self, *, inject_pulses, autoload_pulses, filename):
        if inject_pulses is not None:
            inject_pulses = normalize_native_gates(inject_pulses)
        self.inject_pulses = inject_pulses
        self.autoload_pulses = autoload_pulses
        self.filename = filename

        self.gate_memo = GateMemoizer()

    def build(self, expression, context=None, gate_context=None):
        """Build the appropriate thing based on the expression."""
        if context is None:
            context = self.make_context()
        if gate_context is None:
            gate_context = self.make_gate_context()
        if isinstance(expression, str):
            # Identifiers
            if expression in context:
                return context[expression]
            raise JaqalError(f"Identifier {expression} not found in context")
        if not SExpression.is_convertible(expression):
            # This is either a number used as a gate argument or an already-created type.
            return expression
        sexpression = SExpression(expression)
        method_name = f"build_{sexpression.command}"
        if not hasattr(self, method_name):
            raise JaqalError(f"Cannot handle object of type {sexpression.command}")
        return getattr(self, method_name)(sexpression, context, gate_context)

    def make_context(self):
        """Return a context dictionary consisting of elements given in the constructor."""
        return {}

    def make_gate_context(self):
        """Return a context dictionary consisting of gates given in the constructor."""
        gate_context = {}
        if self.inject_pulses:
            gate_context.update(self.inject_pulses)
        return gate_context

    def build_circuit(self, sexpression, context, gate_context):
        """Build a Circuit object."""
        # registers also include register aliases defined with the map statement
        registers = {}
        constants = {}
        macros = {}
        statements = []
        usepulses = []
        native_gates = gate_context.copy()

        for expr in sexpression.args:
            obj = self.build(expr, context, gate_context)
            if isinstance(obj, Register) or isinstance(obj, NamedQubit):
                # A Register is a register or map and a NamedQubit is a map of a single qubit.
                registers[obj.name] = obj
                self.add_to_context(context, obj.name, obj)
            elif isinstance(obj, Constant):
                constants[obj.name] = obj
                self.add_to_context(context, obj.name, obj)
            elif isinstance(obj, Macro):
                obj = rebuild_macro_in_context(obj, context, gate_context)
                macros[obj.name] = obj
                self.add_to_context(gate_context, obj.name, obj)
            elif (
                isinstance(obj, GateStatement)
                or isinstance(obj, BlockStatement)
                or isinstance(obj, LoopStatement)
                or isinstance(obj, BranchStatement)
                or isinstance(obj, CaseStatement)
            ):
                statements.append(obj)
            elif isinstance(obj, UsePulsesStatement):
                usepulses.append(obj)
                if self.autoload_pulses:
                    obj.update_gates(gate_context, inject_pulses=self.inject_pulses)
                    obj.update_gates(native_gates, inject_pulses=self.inject_pulses)
            else:
                raise JaqalError(f"Cannot process object {obj} at circuit level")

        circuit = Circuit(native_gates=native_gates)
        circuit.registers.update(registers)
        circuit.constants.update(constants)
        circuit.macros.update(macros)
        circuit.body.statements.extend(statements)
        circuit.usepulses.extend(usepulses)
        return circuit

    def add_to_context(self, context, name, obj):
        if name in context:
            raise JaqalError(f"Object {obj} already exists in context")
        context[name] = obj

    @contextmanager
    def in_block_context(self, context, name):
        """Mark us as being in a certain kind of block context."""
        context_name = f"__in_context_{name}__"
        old_value = context.get(context_name)
        context[context_name] = True
        try:
            yield
        finally:
            if old_value is None:
                del context[context_name]
            else:
                context[context_name] = old_value

    def is_in_block_context(self, context, names):
        """Return if we are in any block context given in names."""
        if isinstance(names, str):
            names = [names]
        names = [f"__in_context_{name}__" for name in names]
        return any(context.get(name, False) for name in names)

    def build_register(self, sexpression, context, gate_context):
        """Create a qubit register."""
        name, size = sexpression.args
        size = self.build(size, context, gate_context)  # Resolve let-constants
        return Register(name, size)

    def build_map(self, sexpression, context, gate_context):
        args = list(sexpression.args)
        if len(args) > 1:
            if isinstance(args[1], Register):
                src = args[1]
            else:
                try:
                    name, src_name = args[:2]
                    src = context[src_name]
                except KeyError:
                    raise JaqalError(
                        f"Cannot map {src_name} to {name}, {src_name} does not exist"
                    )
        if len(args) == 2:
            # Mapping a whole register or alias onto this alias
            name, src_name = args
            return Register(name, alias_from=src)
        if len(args) == 3:
            # Mapping a single qubit
            name, src_name, src_index = args
            index = self.build(
                src_index, context
            )  # This may be either an integer or defined parameter.
            return NamedQubit(name, src, index)
        if len(args) == 5:
            # Mapping a slice of a register
            name, src_name, src_start, src_stop, src_step = args
            # These may be either integers, None, or let constants
            start = self.build(src_start, context, gate_context)
            if start is None:
                start = 0
            stop = self.build(src_stop, context, gate_context)
            if stop is None:
                stop = src.size
            step = self.build(src_step, context, gate_context)
            if step is None:
                step = 1
            return Register(name, alias_from=src, alias_slice=slice(start, stop, step))
        raise JaqalError(f"Wrong number of arguments for map, found {args}")

    def build_let(self, sexpression, _context, _gate_context):
        args = list(sexpression.args)
        if len(args) != 2:
            raise JaqalError(f"let statement requires two arguments, found {args}")
        name, value = args
        return Constant(name, as_integer(value))

    def build_macro(self, sexpression, context, gate_context):
        args = list(sexpression.args)
        if len(args) < 2:
            raise JaqalError(f"Macro must have at least two arguments, found {args}")
        name = args[0]
        if name in gate_context:
            raise JaqalError(f"Attempting to redefine gate {name}")
        parameter_args = args[1:-1]
        block = args[-1]
        parameter_list = [
            param if isinstance(param, Parameter) else Parameter(param, None)
            for param in parameter_args
        ]
        parameter_dict = {param.name: param for param in parameter_list}
        macro_context = {
            **context,
            **parameter_dict,
        }  # parameters must be listed second to take precedence
        built_block = self.build(block, macro_context, gate_context)
        if not isinstance(built_block, BlockStatement):
            raise JaqalError(f"Macro body must be a block, found {type(built_block)}")
        return Macro(name, parameters=parameter_list, body=built_block)

    def build_gate(self, sexpression, context, gate_context):
        gate_name, *gate_args = sexpression.args
        gate, memo_key = self.gate_memo.get(gate_name, gate_args, context)
        if gate is None:
            gate_def = self.get_gate_definition(gate_name, len(gate_args), gate_context)
            built_args = (self.build(arg, context, gate_context) for arg in gate_args)
            gate = gate_def(*built_args)
            self.gate_memo.set(memo_key, gate)
        return gate

    def get_gate_definition(self, name, arg_count, gate_context):
        """Return the definition for the given gate. If no such definition exists, and we
        aren't requiring all gates to be a native gate or macro, then create a new
        definition and return it."""
        if name in gate_context:
            gate_def = gate_context[name]
            if not isinstance(gate_def, AbstractGate):
                raise JaqalError(
                    f"Cannot call gate {name}: it is type {type(gate_def)}"
                )
            return gate_def

        is_anonymous_gate_allowed = (
            self.inject_pulses is None
        ) and not self.autoload_pulses

        if not is_anonymous_gate_allowed:
            raise JaqalError(f"No gate {name} defined")
        gate_def = GateDefinition(
            name, parameters=[Parameter(f"p{i}", None) for i in range(arg_count)]
        )
        gate_context[name] = gate_def
        return gate_def

    def build_loop(self, sexpression, context, gate_context):
        count, block = sexpression.args
        built_count = self.build(count, context, gate_context)
        built_block = self.build(block, context, gate_context)
        return LoopStatement(built_count, built_block)

    def build_branch(self, sexpression, context, gate_context):
        cases = sexpression.args
        built_cases = [self.build(b, context, gate_context) for b in cases]
        return BranchStatement(built_cases)

    def build_case(self, sexpression, context, gate_context):
        state, block = sexpression.args
        built_state = self.build(state, context, gate_context)
        built_block = self.build(block, context, gate_context)
        return CaseStatement(built_state, built_block)

    def build_sequential_block(self, sexpression, context, gate_context):
        return self.build_block(sexpression, context, gate_context, is_parallel=False)

    def build_parallel_block(self, sexpression, context, gate_context):
        return self.build_block(sexpression, context, gate_context, is_parallel=True)

    def build_subcircuit_block(self, sexpression, context, gate_context):
        if self.is_in_block_context(context, ["subcircuit", "parallel"]):
            raise JaqalError("Nesting subcircuit in subcircuit or parallel block")
        args = list(sexpression.args)
        with self.in_block_context(context, "subcircuit"):
            statements = [self.build(arg, context, gate_context) for arg in args[1:]]
            count = args[0]
            if count == "":
                built_count = 1
            else:
                built_count = self.build(count, context, gate_context)
        return BlockStatement(
            statements=statements, subcircuit=True, iterations=built_count
        )

    def build_unscheduled_block(self, sexpression, context, gate_context):
        # This is not API, and is strictly for internal use (by extras) at the moment.
        statements = [
            self.build(arg, context, gate_context) for arg in sexpression.args
        ]
        return UnscheduledBlockStatement(parallel=False, statements=statements)

    def build_block(self, sexpression, context, gate_context, is_parallel=False):
        # Note: Unlike at the circuit level statements here can't affect the context (i.e. we can't define
        # a macro inside of a block).
        typename = "parallel" if is_parallel else "sequential"
        with self.in_block_context(context, typename):
            statements = [
                self.build(arg, context, gate_context) for arg in sexpression.args
            ]
        return BlockStatement(parallel=is_parallel, statements=statements)

    def build_array_item(self, sexpression, context, gate_context):
        identifier, index = sexpression.args
        built_identifier = self.build(identifier, context, gate_context)
        built_index = as_integer(self.build(index, context, gate_context))
        # If built_identifier is the wrong type it will raise its own JaqalError, or at least it should.
        return built_identifier[built_index]

    def build_usepulses(self, sexpression, context, gate_context):
        name, filt = sexpression.args

        # XXX: Parse this list of gates to import when we fully implement usepulses
        if (filt is not all) and (filt != "*"):
            raise JaqalError("Only from ... usepulses * currently supported.")

        return UsePulsesStatement(name, all, filename=self.filename)


def rebuild_macro_in_context(macro, context, gate_context):
    """Rebuild a built macro with the given context. This allows this
    macro to refer to other macros that were unknown to it when it was
    originally built.

    Return a new Macro object, sharing as much substructure as
    possible with the input. If the input requires no rebuilding, it
    will be returned unchanged.

    """

    visitor = RebuildMacroInContextVisitor(context, gate_context)
    _changed, new_macro = visitor.visit(macro)
    return new_macro


class RebuildMacroInContextVisitor(Visitor):
    """Rebuild a macro in some context. The only changes that need to be
    made are to create a new gate if the old one referenced a macro in
    the context. All other statements merely repackage changed
    gates. Anything not listed is not possible in a macro or too low
    level (e.g. identifiers).

    """

    def __init__(self, context, gate_context):
        self.context = context
        self.gate_context = gate_context

    def visit_Macro(self, macro):
        changed, new_body = self.visit(macro.body)
        if changed:
            return changed, Macro(macro.name, macro.parameters, new_body)
        else:
            return changed, macro

    def visit_BlockStatement(self, block):
        changed = False
        new_statements = []
        for stmt in block.statements:
            stmt_changed, new_stmt = self.visit(stmt)
            changed = changed or stmt_changed
            new_statements.append(new_stmt)
        if changed:
            return changed, BlockStatement(
                parallel=block.parallel, statements=new_statements
            )
        else:
            return changed, block

    def visit_LoopStatement(self, loop):
        changed, new_statements = self.visit(loop.statements)
        if changed:
            return changed, LoopStatement(loop.iterations, new_statements)
        else:
            return changed, loop

    def visit_BranchStatement(self, branch):
        changed = False
        new_cases = []
        for case in branch.cases:
            case_changed, new_case = self.visit(case)
            changed = changed or case_changed
            new_cases.append(new_case)
        if changed:
            return changed, BranchStatement(cases=new_cases)
        else:
            return changed, branch

    def visit_CaseStatement(self, case):
        changed, new_statements = self.visit(case.statements)
        if changed:
            return changed, CaseStatement(case.state, new_statements)
        else:
            return changed, case

    def visit_GateStatement(self, gate):
        gate_def = self.gate_context.get(gate.name)
        if gate_def is None:
            # Shouldn't happen but really none of our business here.
            return False, gate
        if isinstance(gate_def, Macro):
            if gate_def == gate.gate_def:
                return False, gate

            args = gate.parameters.values()
            new_gate = gate_def(*args)
            return True, new_gate
        else:
            return False, gate


class GateMemoizer:
    """Helper class for memoizing gates within a context."""

    def __init__(self):
        self._table = {}

    def get(self, gate_name, gate_args, context):
        """Find a previously memoized gate with the same name and args, taking
        the context into account. Return the gate and the key under
        which it was found. Return None for the gate if it was not in
        the memo table.

        """

        memo_key = self._make_gate_memo_key(gate_name, gate_args, context)
        gate = self._table.get(memo_key)
        return gate, memo_key

    def set(self, memo_key, gate):
        """Store the create gate in the memo table."""
        self._table[memo_key] = gate

    def _make_gate_memo_key(self, gate_name, gate_args, context):
        """Create a key uniquely identifying the given gate within some
        context."""
        # We take the context into account by creating a tuple of
        # corresponding values in the context or None if they don't
        # appear in the current context.
        def make_context_entry(arg):
            if isinstance(arg, str):
                return context.get(arg)
            else:
                return None

        memo_key = (
            gate_name,
            self._make_hashable(gate_args),
            tuple(make_context_entry(arg) for arg in gate_args),
        )
        return memo_key

    @classmethod
    def _make_hashable(cls, obj):
        """Basically just replace all lists with tuples, recursively."""
        if isinstance(obj, (list, tuple)):
            return tuple(cls._make_hashable(v) for v in obj)
        else:
            return obj


def as_integer(value):
    """Return the given value as an integer if possible."""
    try:
        int_value = int(value)
        if value == int_value:
            return int_value
    except Exception:
        # The value wasn't even numeric.
        pass
    return value


class SExpression:
    """Represent an s-expression as used internally in the builder object.

    By processing the expression and not directly using the tuple or list we give
    ourselves the opportunity to do things like add lisp-style keyword arguments or do
    other things without breaking existing code.
    """

    @classmethod
    def is_convertible(cls, obj):
        """Return whether the object can be converted to an SExpression"""
        return isinstance(obj, tuple) or isinstance(obj, list) or isinstance(obj, cls)

    @classmethod
    def create(cls, expr):
        """Create a new SExpression, or return the argument if it already is one."""
        if isinstance(expr, cls):
            return expr
        return cls(expr)

    def __init__(self, expression):
        if not isinstance(expression, tuple) and not isinstance(expression, list):
            # Make sure you use the create() method as it accepts slightly more types.
            raise JaqalError(
                f"Need tuple or list to make SExpression, found {expression}"
            )
        if len(expression) < 1 or not isinstance(expression[0], str):
            raise JaqalError(
                f"SExpression first element must be a string, found {expression}"
            )
        self._expression = expression

    @property
    def command(self):
        """Return the command portion of the s-expression."""
        return self._expression[0]

    @property
    def args(self):
        """Iterate over the arguments of this s-expression."""
        arg_iter = iter(self._expression)
        next(arg_iter)
        return arg_iter


##
# Object-oriented interface
#


class BlockBuilder:
    """Base class for several other builder objects. Stores statements and other blocks
    in a block."""

    def __init__(self, name):
        self._expression = [name]

    @property
    def expression(self):
        """Return the expression being built, as a list."""
        return self._expression

    def build(self, inject_pulses=None, autoload_pulses=False, filename=None):
        """Create a circuit.

        Recursively construct an immutable core object of the appropriate type, as
        described by this Builder.

        :param inject_pulses: If given, use these pulses specifically.
        :param bool autoload_pulses: Whether to employ the usepulses statement for
            parsing.  Requires appropriate gate definitions.
        :param str filename: The effective location of the Jaqal file, used for
            relative imports.
        :return: An appropriate core type object.

        """
        return build(
            self.expression,
            inject_pulses=inject_pulses,
            autoload_pulses=autoload_pulses,
            filename=filename,
        )

    def gate(self, name, *args, no_duplicate=False):
        """Add a gate to this block.

        :param str name: The name of the gate.
        :param args: Any arguments to the gate.
        :param bool no_duplicate: If True, only add this gate if it is not a duplicate of
            the gate to go right before it (or it is the first gate).
        """
        # Note: the gate expression will accept both core types and other s-expressions.
        gate_expression = ("gate", name, *args)
        if no_duplicate and self.expression and self.expression[-1] == gate_expression:
            return
        self.expression.append(gate_expression)

    def block(self, parallel=False):
        """Create, add, and return a new block builder to the statements stored in this
        block. Although it is not legal in Jaqal to nest blocks of the same type (except
        at top level), this builder ignores that restriction.

        To create a block builder without adding it to this block, use the appropriate
        class constructor directly. This is useful when creating a macro or loop.

        :param parallel: Set to False (default) for a sequential block, True for a
            parallel block.
        :type parallel: bool or None
        :returns: The new block builder.
        :rtype: SequentialBlockBuilder or ParallelBlockBuilder
        """

        builder = SequentialBlockBuilder() if not parallel else ParallelBlockBuilder()
        self.expression.append(builder.expression)
        return builder

    def subcircuit(self, iterations=None):
        """Create, add, and return a new block builder to the statements stored in this
        block. Although it is not legal in Jaqal to nest certain blocks, this builder
        ignores these restrictions.

        To create a subcircuit builder without adding it to this block, use the
        SubcircuitBlockBuilder class directly.

        :param iterations: The number of times to run this on the
            hardware to accumulate statistics.
        :type iterations: int, str, AnnotatedValue, or None
        """

        builder = SubcircuitBlockBuilder()
        self.expression.append(builder.expression)
        return builder

    def loop(self, iterations, block, unevaluated=False):
        """Creates a new :class:`LoopStatement` object, and adds it to the end of this
        block.

        :param int iterations: How many times to repeat the loop.
        :param block: The contents of the loop. If a :class:`BlockStatement` is passed,
            it will be used as the loop's body. A :class:`BlockBuilder` may also be
            passed, in which case the block it builds will be used as the loop's body.
        :type block: BlockStatement, BlockBuilder
        :param bool unevaluated: If False, do not create a LoopStatement object to return.
        :returns: The new loop.
        :rtype: LoopStatement
        """

        if isinstance(block, BlockBuilder):
            block = block.expression
        loop = ("loop", iterations, block)
        if not unevaluated:
            loop = build(loop)
        self.expression.append(loop)
        return loop

    def branch(self):
        builder = BranchBlockBuilder()
        self.expression.extend(builder.expression)
        return builder

    def case(self, state, block):
        if isinstance(block, BlockBuilder):
            block = block.expression
        case = ("case", state, block)
        case = build(case)
        self.expression.append(case)
        return case


class SequentialBlockBuilder(BlockBuilder):
    """Build up a sequential code block."""

    def __init__(self):
        super().__init__("sequential_block")


class ParallelBlockBuilder(BlockBuilder):
    """Build up a parallel code block."""

    def __init__(self):
        super().__init__("parallel_block")


class SubcircuitBlockBuilder(BlockBuilder):
    """Build up a subcircuit code block."""

    def __init__(self, iterations=None):
        super().__init__("subcircuit_block")
        self.expression.append(iterations)


class BranchBlockBuilder(BlockBuilder):
    """Build up a sequential code block."""

    def __init__(self):
        super().__init__("branch")


class CaseBlockBuilder(BlockBuilder):
    """Build up a sequential code block."""

    def __init__(self):
        super().__init__("case")


# This is not API currently, but is used by jaqalpaq-extras for automatic scheduling.
class UnscheduledBlockBuilder(BlockBuilder):
    """Build up an unscheduled code block."""

    def __init__(self):
        super().__init__("unscheduled_block")


class CircuitBuilder(BlockBuilder):
    """Object-oriented interface to the build() command. Build up a circuit from its
    components and then create a full Circuit on demand.

    Unlike in legal Jaqal, we allow intermixing of body and header statements.
    """

    def __init__(self, native_gates=None):
        super().__init__("circuit")
        self.native_gates = native_gates
        self._fundamental_register_index = None

    def build(self, context=None):
        """Override the build method to provide the native gates."""
        if context is not None:
            raise JaqalError(
                "Do not provide a context to the build method of CircuitBuilder"
            )
        return super().build(self.native_gates)

    def usepulses(self, module, names=all, unevaluated=False):
        """Allocates a new :class:`UsePulsesStatement` representing the given
        pulse file.

        :param str module: the . delineated module path
        :param list[str] names: either the special value `all`, or a list of tokens to import
        :param bool unevaluated: If False, do not create a UsePulsesStatement object to return.
        :returns: The new usepulses import.
        """

        usepulses = ("usepulses", module, names)
        if not unevaluated:
            usepulses = build(usepulses)
        self.expression.append(usepulses)
        return usepulses

    def register(self, name, size, unevaluated=False):
        """
        Allocates a new fundamental :class:`Register` of the given size, adding it to the
        circuit under the given name. Equivalent to the Jaqal header statement
        :samp:`register {name}[{size}]`.

        :param str name: The name of the register.
        :param int size: How many qubits are in the register.
        :param bool unevaluated: If False, do not create a Register object to return.
        :returns: The new register.
        """

        register = ("register", name, size)
        if not unevaluated:
            register = build(register)
        self._fundamental_register_index = len(self.expression)
        self.expression.append(register)
        return register

    def let(self, name, value, unevaluated=False):
        """
        Creates a new :class:`Constant`, mapping the given name to the given value, and
        adds it to the circuit. Equivalent to the Jaqal header statement
        :samp:`let {name} {value}`.

        :param str name: The name of the new constant.
        :param value: The numeric value of the new constant.
        :type value: int or float
        :param bool unevaluated: If False, do not create a Register object to return.
        :returns: The new object.
        """
        constant = ("let", name, value)
        if not unevaluated:
            constant = build(constant)
        self.expression.append(constant)
        return constant

    def map(self, name, source, idxs=None, unevaluated=False):
        """
        Creates a new :class:`Register` (or :class:`NamedQubit`, if idxs is a single index
        rather than a slice) mapped to some subset of an existing register, and adds it to
        the circuit. Equivalent to the Jaqal header statement
        :samp:`map {name} {source}[{idxs}]`.

        :param str name: The name of the new register.
        :param source: The source register to map the new register onto, or its name.
        :type source: Register or str
        :param idxs: Which qubits in the source register to map. If None, map the entire
            register.
        :type idxs: slice, int, AnnotatedValue, str, or None
        :param bool unevaluated: If False, do not create a Register object to return.
        :returns: The new register.
        :rtype: Register or NamedQubit
        """
        if idxs is None:
            register = ("map", name, source)
        elif isinstance(idxs, slice):
            register = ("map", name, source, idxs.start, idxs.stop, idxs.step)
        else:
            register = ("map", name, source, idxs)
        if not unevaluated:
            register = build(register)
        self.expression.append(register)
        return register

    def macro(self, name, parameters=None, body=None, unevaluated=False):
        """
        Defines a :class:`Macro` and adds it to the circuit. Equivalent to the Jaqal
        statement :samp:`macro {name} {parameters} \{{body}\}`.

        :param str name: The name of the macro.
        :param list parameters: What arguments (numbers, qubits, etc) the macro should be
            called with. If None, the macro takes no parameters.
        :param body: What statements the macro expands to when called. This may also be a
            BlockBuilder.
        :param bool unevaluated: If False, do not create a Macro object to return.
        :returns: The new macro.
        :rtype: Macro
        :raises JaqalError: if the name of the macro or any of its parameters is invalid
            (see :meth:`validate_identifier`).
        """

        parameters = parameters or []
        if isinstance(body, BlockBuilder):
            body = body.expression
        macro = ("macro", name, *parameters, body)
        if not unevaluated:
            macro = build(macro)
        self.expression.append(macro)
        return macro

    def stretch_register(self, new_size):
        """
        If this circuit has a fundamental register smaller than ``new_size``, increase its
        size to ``new_size``.

        :param int new_size: How large the register should become.
        :returns: True if the register now contains exactly ``new_size`` qubits, False if
            the register previously contained and still contains more than that.
        :rtype: bool
        :raises JaqalError: If the circuit does not have a fundamental register.
        """

        if self._fundamental_register_index is None:
            raise JaqalError("No fundamental register to stretch.")
        register = self.expression[self._fundamental_register_index]
        if isinstance(register, Register):
            old_size = register.size
            old_name = register.name
            if old_size < new_size:
                register._size = new_size
        else:
            old_size = register[2]
            old_name = register[1]
            if old_size < new_size:
                self.expression[self._fundamental_register_index] = (
                    "register",
                    old_name,
                    new_size,
                )

        return new_size >= old_size
