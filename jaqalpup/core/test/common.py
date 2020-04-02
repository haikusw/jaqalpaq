import random
import math

from jaqalpup.core import (
    Register, Constant, NamedQubit, PARAMETER_TYPES, Parameter, GateDefinition,
    FLOAT_TYPE, INT_TYPE, QUBIT_TYPE, REGISTER_TYPE, Macro, BlockStatement,
    GateStatement
)
from .randomize import (
    random_identifier, random_whole, random_integer, random_float
)

VALID_GATE_ARG_TYPES = [FLOAT_TYPE, INT_TYPE, QUBIT_TYPE]


def assert_values_same(tester, value0, value1, message=None):
    """Return if two values, which could be a floating point nan, are the
    same. Invokes an appropriate assert macro on tester."""
    if math.isnan(value0):
        tester.assertTrue(math.isnan(value1), message)
    else:
        tester.assertEqual(value0, value1, message)


def make_random_parameter(name=None, allowed_types=None, return_params=False):
    """Return a parameter with a random type and name."""
    if name is None:
        name = random_identifier()
    if allowed_types is None:
        allowed_types = PARAMETER_TYPES
    param_type = random.choice(allowed_types)
    if param_type not in PARAMETER_TYPES:
        raise ValueError(f"Unknown parameter type {param_type}")
    param = Parameter(name, param_type)
    if not return_params:
        return param
    else:
        return param, name, param_type


def make_random_parameter_list(allowed_types=None, count=None):
    """Return a list of Parameter objects."""
    if allowed_types is None:
        allowed_types = PARAMETER_TYPES
    if count is None:
        count = random_integer(lower=0, upper=16)
    param_list = []
    names_used = set()
    for _ in range(count):
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
        const_type = random.choice([FLOAT_TYPE, INT_TYPE])
        if const_type == FLOAT_TYPE:
            value = random_float()
        elif const_type == INT_TYPE:
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
        index = random_integer(lower=0, upper=reg.size - 1)
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
    start = random_whole(upper=upper - 1)
    length = random_whole(upper=(upper - start))
    step = random_whole(upper=16)
    return slice(start, start + length, step)


def make_random_gate_definition(name=None, parameter_count=None, return_params=False):
    """Create a random gate definition."""
    if name is None:
        name = random_identifier()
    if parameter_count is None:
        parameter_count = random_integer(lower=0, upper=16)
    allowed_types = VALID_GATE_ARG_TYPES + [None]
    parameters = make_random_parameter_list(count=parameter_count, allowed_types=allowed_types)
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
    if value_type is None:
        value_type = random.choice([INT_TYPE, FLOAT_TYPE, REGISTER_TYPE, QUBIT_TYPE])
    if value_type == INT_TYPE:
        return random_integer()
    elif value_type == FLOAT_TYPE:
        return random_float()
    elif value_type == REGISTER_TYPE:
        return make_random_register()
    elif value_type == QUBIT_TYPE:
        reg = make_random_register()
        return choose_random_qubit_getitem(reg)
    else:
        raise ValueError(f"Unknown value type {value_type}")


def make_random_macro_definition(name=None, parameter_count=None, body_count=None, return_params=False, return_body=False):
    """Create a random macro definition."""
    if name is None:
        name = random_identifier()
    if parameter_count is None:
        parameter_count = random_integer(lower=0, upper=16)
    if body_count is None:
        # I think the most interesting difference will be between no statements and any
        # statements, so bias this towards producing no statements
        if random.uniform(0, 1) < 0.1:
            body_count = 0
        else:
            body_count = random_whole(upper=100)
    allowed_types = [None]  # In Jaqal we don't declare types for macros
    parameters = make_random_parameter_list(count=parameter_count, allowed_types=allowed_types)
    body = make_random_sequential_block(count=body_count)
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


def make_random_sequential_block(*, count=None):
    """Create a BlockStatement with some number of random statements."""
    statements = [make_random_gate_statement() for _ in range(count)]
    return BlockStatement(parallel=False, statements=statements)


def make_random_gate_statement(*, count=None):
    """Make a gate statement with random arguments. It will not be based on
    a GateDefinition."""
    if count is None:
        count = random_whole(upper=16)
    name = random_identifier()
    arguments = {
        random_identifier(): make_random_value(random.choice(VALID_GATE_ARG_TYPES))
        for _ in range(count)
    }
    return GateStatement(name, parameters=arguments)