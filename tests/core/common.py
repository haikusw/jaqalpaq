import random
import math

from jaqalpaq.core import (
    Register,
    Constant,
    NamedQubit,
    ParamType,
    Parameter,
    GateDefinition,
    Macro,
    BlockStatement,
    GateStatement,
    LoopStatement,
)
from jaqalpaq.core.branch import BranchStatement, CaseStatement
from .randomize import random_identifier, random_whole, random_integer, random_float

VALID_GATE_ARG_TYPES = [ParamType.FLOAT, ParamType.INT, ParamType.QUBIT]


def assert_values_same(tester, value0, value1, message=None):
    """Return if two values, which could be a floating point nan, are the
    same. Invokes an appropriate assert macro on tester."""
    if isinstance(value0, float) and math.isnan(value0):
        tester.assertTrue(isinstance(value1, float) and math.isnan(value1), message)
    else:
        tester.assertEqual(value0, value1, message)


def make_random_parameter(name=None, allowed_types=None, return_params=False):
    """Return a parameter with a random type and name."""
    if name is None:
        name = random_identifier()
    if allowed_types is None:
        allowed_types = ParamType.types
    param_type = random.choice(allowed_types)
    if param_type not in ParamType:
        raise ValueError(f"Unknown parameter type {param_type}")
    param = Parameter(name, param_type)
    if not return_params:
        return param
    else:
        return param, name, param_type


def make_random_parameter_list(*, parameter_types=None, allowed_types=None, count=None):
    """Return a list of Parameter objects."""
    if parameter_types is not None:
        if allowed_types is not None:
            raise ValueError(f"allowed_types is ignored if parameter_types is given")
        if count is not None:
            raise ValueError("count is ignored if parameter_types is given")
        allowed_types = None
        count = len(parameter_types)
    else:
        if allowed_types is None:
            allowed_types = ParamType.types
        if count is None:
            count = random_integer(lower=0, upper=16)
    param_list = []
    names_used = set()
    for _ in range(count):
        if parameter_types is not None:
            allowed_types = [parameter_types.pop(0)]
        while True:
            param = make_random_parameter(allowed_types=allowed_types)
            if param.name not in names_used:
                names_used.add(param.name)
                break
        param_list.append(param)
    return param_list


def make_random_constant(name=None, value=None, return_params=False):
    """Make a random Constant value."""
    if name is None:
        name = random_identifier()
    if value is None:
        const_type = random.choice([ParamType.FLOAT, ParamType.INT])
        if const_type == ParamType.FLOAT:
            value = random_float()
        elif const_type == ParamType.INT:
            value = random_integer()
        else:
            assert False
    const = Constant(name, value)
    if not return_params:
        return const
    else:
        return const, name, value


def make_random_register(name=None, size=None, return_params=False):
    """Make a random register"""
    if name is None:
        name = random_identifier()
    if size is None:
        size = random_whole()
    reg = Register(name, size)
    if not return_params:
        return reg
    else:
        return reg, name, size


def make_random_size_constant(name=None, value=None, return_params=False):
    """Make a random Constant that can represent a size"""
    if name is None:
        name = random_identifier()
    if value is None:
        value = random_whole()
    const = Constant(name, value)
    if not return_params:
        return const
    else:
        return const, name, value


def choose_random_qubit_getitem(reg, index=None, return_params=False):
    """Choose a random qubit from a register with its getitem special method."""
    if index is None:
        index = random_integer(lower=0, upper=int(reg.size) - 1)
    qubit = reg[index]
    if not return_params:
        return qubit
    else:
        return qubit, index


def choose_random_qubit_init(reg, name=None, index=None, return_params=False):
    """Choose a random qubit from a register using the NamedQubit's constructor."""
    if index is None:
        index = random_integer(lower=0, upper=reg.size - 1)
    if name is None:
        name = random_identifier()
    qubit = NamedQubit(name, reg, index)
    if not return_params:
        return qubit
    else:
        return qubit, name, index


def make_qubit_name(reg, index):
    return f"{reg.name}[{index}]"


def make_map_full(reg, name=None, return_params=False):
    """Make a map alias to the given register."""
    if name is None:
        name = random_identifier()
    map_reg = Register(name, alias_from=reg)
    if not return_params:
        return map_reg
    else:
        return map_reg, name


def make_map_slice(reg, name=None, map_slice=None, return_params=False):
    """Make a map alias to a slice of the given register."""
    if name is None:
        name = random_identifier()
    if map_slice is None:
        map_slice = make_random_slice(reg.size)
    map_reg = Register(name, alias_from=reg, alias_slice=map_slice)
    if not return_params:
        return map_reg
    else:
        return map_reg, name, map_slice


def make_random_slice(upper):
    """Return a slice of an array with upper bound upper. Guaranteed to have
    at least one element."""
    start = random_integer(lower=0, upper=upper - 1)
    length = random_whole(upper=(upper - start))
    step = random_whole(upper=16)
    return slice(start, start + length, step)


def make_random_gate_definition(
    name=None, parameter_count=None, parameter_types=None, return_params=False
):
    """Create a random gate definition."""
    if name is None:
        name = random_identifier()
    if parameter_types is None:
        if parameter_count is None:
            parameter_count = random_integer(lower=0, upper=16)
        allowed_types = VALID_GATE_ARG_TYPES + [ParamType.NONE]
        parameters = make_random_parameter_list(
            count=parameter_count, allowed_types=allowed_types
        )
    else:
        parameters = make_random_parameter_list(parameter_types=parameter_types)
    gatedef = GateDefinition(name, parameters=parameters)
    if not return_params:
        return gatedef
    else:
        return gatedef, name, parameters


def make_random_argument_list(argument_types):
    """Return a list of randomly produced gate arguments of the appropriate type.
    For any value whatsoever, use the None type. Note: This will never create
    a register since that is not a valid Jaqal gate argument."""
    arguments = []
    for arg_type in argument_types:
        if arg_type is None:
            arg_type = random.choice(VALID_GATE_ARG_TYPES)
        arg = make_random_value(arg_type)
        arguments.append(arg)
    return arguments


def make_random_value(value_type):
    """Create a random value of the given type.

    Note that registers and qubits will just be their own thing and not
    tied to any existing objects.

    Note that in the case of a float, this can return nan and inf."""
    if value_type == ParamType.NONE:
        value_type = random.choice(
            [ParamType.INT, ParamType.FLOAT, ParamType.REGISTER, ParamType.QUBIT]
        )
    if value_type == ParamType.INT:
        return random_integer()
    elif value_type == ParamType.FLOAT:
        return random_float()
    elif value_type == ParamType.REGISTER:
        return make_random_register()
    elif value_type == ParamType.QUBIT:
        reg = make_random_register()
        return choose_random_qubit_getitem(reg)
    else:
        raise ValueError(f"Unknown value type {value_type}")


def make_random_macro_definition(
    name=None,
    parameter_count=None,
    body_count=None,
    body=None,
    return_params=False,
    return_body=False,
):
    """Create a random macro definition."""
    if name is None:
        name = random_identifier()
    if parameter_count is None:
        parameter_count = random_integer(lower=0, upper=16)
    if body is None:
        if body_count is None:
            # I think the most interesting difference will be between no statements and any
            # statements, so bias this towards producing no statements
            if random.uniform(0, 1) < 0.1:
                body_count = 0
            else:
                body_count = random_whole(upper=100)
        body = make_random_block(count=body_count)
    allowed_types = [ParamType.NONE]  # In Jaqal we don't declare types for macros
    parameters = make_random_parameter_list(
        count=parameter_count, allowed_types=allowed_types
    )
    gatedef = Macro(name, body=body, parameters=parameters)
    if not return_params:
        if not return_body:
            return gatedef
        else:
            return gatedef, body
    else:
        if not return_body:
            return gatedef, name, parameters
        else:
            return gatedef, name, parameters, body


def make_random_block(*, count=None, parallel=False, return_params=False):
    """Create a BlockStatement with some number of random statements."""
    if count is None:
        count = random_integer(lower=0, upper=16)
    statements = [make_random_gate_statement() for _ in range(count)]
    block = BlockStatement(parallel=parallel, statements=statements)
    if not return_params:
        return block
    else:
        return block, statements


def make_random_gate_statement(
    *, count=None, parameter_types=None, return_params=False
):
    """Make a gate statement with random arguments based on
    a GateDefinition."""
    definition, _, parameters = make_random_gate_definition(
        parameter_count=count, parameter_types=parameter_types, return_params=True
    )
    arguments = {param.name: make_random_value(param.kind) for param in parameters}
    gate = GateStatement(definition, parameters=arguments)
    if not return_params:
        return gate
    else:
        return gate, definition, arguments


def make_random_loop_statement(
    *, iterations=None, body_count=None, return_params=False
):
    """Make a loop statement with a random number of iterations and body
    statements."""
    if iterations is None:
        iterations = random_whole()
    if body_count is None:
        body_count = random_integer(lower=0, upper=16)
    block = make_random_block(count=body_count)
    loop = LoopStatement(iterations=iterations, statements=block)
    if not return_params:
        return loop
    else:
        return loop, iterations, block


def make_random_branch_statement(*, cases=None, body_count=None, return_params=False):
    """Make a branch statement with a random number of cases and gates in
    those cases."""
    if cases is None:
        cases = random_whole()
    if body_count is None:
        body_count = random_integer(lower=0, upper=16)
    case_statements = [make_random_case(count=body_count) for _ in range(cases)]
    branch = BranchStatement(case_statements)
    if not return_params:
        return branch
    else:
        return branch, body_count, case_statements


def make_random_case(*, count=None, bit_count=None, return_params=False):
    """Make a random case designed for branch statements."""
    if count is None:
        count = random_integer(lower=0, upper=16)
    if bit_count is None:
        # This determines the size of the state select
        bit_count = random_integer(lower=1, upper=4)
    state = random_integer(lower=0, upper=(1 << bit_count) - 1)
    statements = [make_random_gate_statement() for _ in range(count)]
    case = CaseStatement(state=state, statements=statements)
    if not return_params:
        return case
    else:
        return case, state, statements
