# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from jaqalpaq.core import (
    GateStatement,
    BlockStatement,
    LoopStatement,
    Register,
    NamedQubit,
    Constant,
    Parameter,
    AnnotatedValue,
)


def notate_slice(s):
    if s.step:
        return "%s:%s:%s" % (
            generate_jaqal_value(s.start or 0),
            generate_jaqal_value(s.stop),
            generate_jaqal_value(s.step),
        )
    else:
        return "%s:%s" % (
            generate_jaqal_value(s.start or 0),
            generate_jaqal_value(s.stop),
        )


def generate_jaqal_program(circ):
    """
    Converts a :class:`jaqalpaq.core.Circuit` object to the Jaqal program it represents.

    :param Circuit circ: The circuit to output.
    :returns: The text of a Jaqal program that describes that circuit.
    :rtype: str
    """
    program = ""
    for const in circ.constants.values():
        program += generate_jaqal_let(const)
    if circ.constants:
        program += "\n"
    for register in circ.registers.values():
        if register.fundamental:
            program += generate_jaqal_reg(register)
    program += "\n"
    for register in circ.registers.values():
        if not register.fundamental:
            program += generate_jaqal_map(register)
    if len(circ.registers) > 1:
        program += "\n"
    for macro in circ.macros.values():
        program += generate_jaqal_macro(macro)
    for statement in circ.body:
        if isinstance(statement, GateStatement):
            program += generate_jaqal_gate(statement, 0)
        elif isinstance(statement, LoopStatement):
            program += generate_jaqal_loop(statement, 0)
        elif isinstance(statement, BlockStatement):
            program += generate_jaqal_block(statement, 0, True)
    return program


def generate_jaqal_reg(register):
    return "".join(
        ("register ", register.name, "[", generate_jaqal_value(register.size), "]\n")
    )


def generate_jaqal_let(const):
    return "".join(("let ", const.name, " ", generate_jaqal_value(const.value), "\n"))


def generate_jaqal_map(register):
    if isinstance(register, NamedQubit):
        return "".join(
            (
                "map ",
                register.name,
                " ",
                register.alias_from.name,
                "[",
                generate_jaqal_value(register.alias_index),
                "]\n",
            )
        )
    elif register.alias_slice is not None:
        return "".join(
            (
                "map ",
                register.name,
                " ",
                register.alias_from.name,
                "[",
                notate_slice(register.alias_slice),
                "]\n",
            )
        )
    else:
        return "".join(("map ", register.name, " ", register.alias_from.name, "\n"))


def generate_jaqal_macro(macro):
    return "".join(
        (
            "macro ",
            macro.name,
            " ",
            " ".join([parameter.name for parameter in macro.parameters]),
            " ",
            generate_jaqal_block(macro.body, 0, False),
            "\n",
        )
    )


def generate_jaqal_gate(statement, depth):
    return "".join(
        (
            "\t" * depth,
            " ".join(
                (
                    statement.name,
                    *(
                        generate_jaqal_value(val)
                        for val in statement.parameters.values()
                    ),
                )
            ),
            "\n",
        )
    )


def generate_jaqal_loop(statement, depth):
    return "".join(
        (
            "\t" * depth,
            "loop ",
            generate_jaqal_value(statement.iterations),
            " ",
            generate_jaqal_block(statement.statements, depth, False),
        )
    )


def generate_jaqal_block(statement, depth, indent_first_line):
    output = ""
    if indent_first_line:
        output += "\t" * depth
    if statement.parallel:
        output += "<\n"
    else:
        output += "{\n"
    for gate in statement:
        if isinstance(gate, GateStatement):
            output += generate_jaqal_gate(gate, depth + 1)
        elif isinstance(gate, LoopStatement):
            output += generate_jaqal_loop(gate, depth + 1)
        elif isinstance(gate, BlockStatement):
            output += generate_jaqal_block(gate, depth + 1, True)
    output += "\t" * depth
    if statement.parallel:
        output += ">\n"
    else:
        output += "}\n"
    return output


def generate_jaqal_value(val):
    if (
        isinstance(val, Register)
        or isinstance(val, NamedQubit)
        or isinstance(val, AnnotatedValue)
    ):
        return val.name
    elif isinstance(val, float) or isinstance(val, int):
        return str(val)
