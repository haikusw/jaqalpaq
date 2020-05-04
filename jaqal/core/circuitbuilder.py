from typing import Dict

from .constant import Constant
from .macro import Macro
from .register import Register, NamedQubit
from .gate import GateStatement
from .gatedef import GateDefinition, AbstractGate
from .circuit import ScheduledCircuit
from .parameter import Parameter
from .block import BlockStatement, LoopStatement

from jaqal import JaqalError


def build(expression, native_gates=None):
    """Given an expression in a specific format, return the appropriate type, recursively constructed, from the core
    types library.

    :param expression: A tuple acting like an S-expression. Also accepts core types and just returns them.
    :param Dict[str, GateDefinition] native_gates: If given, raise an exception if a gate is not in this list or
    a macro.

    :return: An appropriate core type object.

    Each expression must be an s-expression where the first element defines the type and the rest of the elements define
    the arguments. The signatures are as follows where the first element is before the colon and the remaining are
    space separated after the colon.

    circuit : *elements
    macro : *parameter_names block
    let : identifier value
    register : name size
    map : name [src_name | src_name src_index | src_name src_start src_stop src_step]
    loop : count sequential_block
    gate : *arguments
    sequential_block : *statements
    parallel_block : *statements
    array_item : identifier index

    In lieu of an s-expression, the appropriate type from the core library will also be accepted. This allows to user
    to build up new expressions using partially built old ones.

    Note: the jaqal-pup package partially supports qualified namespaces in identifiers. This function assumes all
    identifiers are one string, that is they are multiple legal identifiers joined by periods.

    """

    builder = Builder(native_gates=native_gates)
    return builder.build(expression)

##
# Private classes and functions. Use the build() function.
#


class Builder:
    """Helper class to recursively build a circuit (or type within it) from s-expressions."""

    def __init__(self, *, native_gates):
        self.native_gates = native_gates

    def build(self, expression, context=None):
        """Build the appropriate thing based on the expression."""
        if context is None:
            context = self.make_context()
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
        return getattr(self, method_name)(sexpression, context)

    def make_context(self):
        """Return a context dictionary consisting of elements given in the constructor."""
        context = {}
        if self.native_gates:
            context.update(self.native_gates)
        return context

    def build_circuit(self, sexpression, context):
        """Build a ScheduledCircuit object."""
        # registers also include register aliases defined with the map statement
        registers = {}
        constants = {}
        macros = {}
        statements = []

        for expr in sexpression.args:
            obj = self.build(expr, context)
            if isinstance(obj, Register) or isinstance(obj, NamedQubit):
                # A Register is a register or map and a NamedQubit is a map of a single qubit.
                registers[obj.name] = obj
                self.add_to_context(context, obj.name, obj)
            elif isinstance(obj, Constant):
                constants[obj.name] = obj
                self.add_to_context(context, obj.name, obj)
            elif isinstance(obj, Macro):
                macros[obj.name] = obj
                self.add_to_context(context, obj.name, obj)
            elif isinstance(obj, GateStatement) or isinstance(obj, BlockStatement) or isinstance(obj, LoopStatement):
                statements.append(obj)
            else:
                raise JaqalError(f"Cannot process object {obj} at circuit level")

        circuit = ScheduledCircuit(native_gates=self.native_gates)
        circuit.registers.update(registers)
        circuit.constants.update(constants)
        circuit.macros.update(macros)
        circuit.body.statements.extend(statements)
        return circuit

    def add_to_context(self, context, name, obj):
        if name in context:
            raise JaqalError(f"Object {obj} already exists in context")
        context[name] = obj

    def build_register(self, sexpression, _context):
        """Create a qubit register."""
        name, size = sexpression.args
        return Register(name, size)

    def build_map(self, sexpression, context):
        args = list(sexpression.args)
        if len(args) == 2:
            # Mapping a whole register or alias onto this alias
            name, src_name = args
            try:
                src = context[src_name]
            except KeyError:
                raise JaqalError(f"Cannot map {src_name} to {name}, {src_name} does not exist")
            return Register(name, alias_from=src)
        if len(args) == 3:
            # Mapping a single qubit
            name, src_name, src_index = args
            try:
                src = context[src_name]
            except KeyError:
                raise JaqalError(f"Cannot map {src_name} to {name}, {src_name} does not exist")
            index = self.build(src_index, context)  # This may be either an integer or defined parameter.
            return NamedQubit(name, src, index)
        if len(args) == 5:
            # Mapping a slice of a register
            name, src_name, src_start, src_stop, src_step = args
            try:
                src = context[src_name]
            except KeyError:
                raise JaqalError(f"Cannot map {src_name} to {name}, {src_name} does not exist")
            # These may be either integers, None, or let constants
            start = self.build(src_start, context)
            stop = self.build(src_stop, context)
            step = self.build(src_step, context)
            return Register(name, alias_from=src, alias_slice=slice(start, stop, step))
        raise JaqalError(f"Wrong number of arguments for map, found {args}")

    def build_let(self, sexpression, _context):
        args = list(sexpression.args)
        if len(args) != 2:
            raise JaqalError(f"let statement requires two arguments, found {args}")
        name, value = args
        return Constant(name, value)

    def build_macro(self, sexpression, context):
        args = list(sexpression.args)
        if len(args) < 2:
            raise JaqalError(f"Macro must have at least two arguments, found {args}")
        name = args[0]
        parameter_names = args[1:-1]
        block = args[-1]
        parameter_list = [Parameter(name, None) for name in parameter_names]
        parameter_dict = {param.name: param for param in parameter_list}
        macro_context = {**context, **parameter_dict}  # parameters must be listed second to take precedence
        built_block = self.build(block, macro_context)
        if not isinstance(built_block, BlockStatement):
            raise JaqalError(f"Macro body must be a block, found {type(built_block)}")
        return Macro(name, parameters=parameter_list, body=built_block)

    def build_gate(self, sexpression, context):
        gate_name, *gate_args = sexpression.args
        gate_def = self.get_gate_definition(gate_name, len(gate_args), context)
        built_args = [self.build(arg, context) for arg in gate_args]
        return gate_def(*built_args)

    def get_gate_definition(self, name, arg_count, context):
        """Return the definition for the given gate. If no such definition exists, and we aren't requiring all gates
        to be a native gate or macro, then create a new definition and return it."""
        if name in context:
            gate_def = context[name]
            if not isinstance(gate_def, AbstractGate):
                raise JaqalError(f"Cannot call gate {name}: it is type {type(gate_def)}")
            return gate_def

        is_anonymous_gate_allowed = (self.native_gates is None)
        if not is_anonymous_gate_allowed:
            raise JaqalError(f"No gate {name} defined")
        gate_def = GateDefinition(name, parameters=[Parameter(f'p{i}', None) for i in range(arg_count)])
        return gate_def

    def build_loop(self, sexpression, context):
        count, block = sexpression.args
        built_count = self.build(count, context)
        built_block = self.build(block, context)
        return LoopStatement(built_count, built_block)

    def build_sequential_block(self, sexpression, context):
        return self.build_block(sexpression, context, is_parallel=False)

    def build_parallel_block(self, sexpression, context):
        return self.build_block(sexpression, context, is_parallel=True)

    def build_block(self, sexpression, context, is_parallel=False):
        # Note: Unlike at the circuit level statements here can't affect the context (i.e. we can't define
        # a macro inside of a block).
        statements = [self.build(arg, context) for arg in sexpression.args]
        return BlockStatement(parallel=is_parallel, statements=statements)

    def build_array_item(self, sexpression, context):
        identifier, index = sexpression.args
        built_identifier = self.build(identifier, context)
        built_index = self.build(index)
        # If built_identifier is the wrong type it will raise its own JaqalError, or at least it should.
        return built_identifier[built_index]


class SExpression:
    """Represent an s-expression as used internally in the builder object.

    By processing the expression and not directly using the tuple we give ourselves the opportunity to do things
    like add lisp-style keyword arguments or do other things without breaking existing code.
    """

    @classmethod
    def is_convertible(cls, obj):
        """Return whether the object can be converted to an SExpression"""
        return isinstance(obj, tuple) or isinstance(obj, cls)

    @classmethod
    def create(cls, expr):
        """Create a new SExpression, or return the argument if it already is one."""
        if isinstance(expr, cls):
            return expr
        return cls(expr)

    def __init__(self, expression):
        if not isinstance(expression, tuple):
            raise JaqalError(f"Need tuple to make SExpression, found {expression}")
        if len(expression) < 1 or not isinstance(expression[0], str):
            raise JaqalError(f"SExpression first element must be a string, found {expression}")
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
