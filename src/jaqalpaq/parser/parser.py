# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from .slyparse import JaqalLexer, JaqalParser, _monkeypatch_sly, HeaderParsingDone
from jaqalpaq.core.algorithm import fill_in_let, expand_macros
from jaqalpaq.core.algorithm.fill_in_map import fill_in_map

from jaqalpaq.core.circuitbuilder import build
from jaqalpaq.error import JaqalError


def parse_jaqal_file(
    filename,
    override_dict=None,
    expand_macro=False,
    expand_let=False,
    expand_let_map=False,
    return_usepulses=False,
    inject_pulses=None,
    autoload_pulses=True,
):
    """Parse a file written in Jaqal into core types.

    :param str filename: The name of the Jaqal file.
    :param override_dict:  An optional dictionary that overrides let statements in the Jaqal code.
        Note: all keys in this dictionary must exist as let statements or an error will be raised.
    :type override_dict: dict[str, float]
    :param bool expand_macro: Replace macro invocations by their body while parsing.
    :param bool expand_let: Replace let constants by their value while parsing.
    :param bool expand_let_map: Replace let constants and mapped qubits while parsing. expand_let is ignored if this is True.
    :param bool return_usepulses: Whether to both add a second return value and populate it with the usepulses statement.
    :param inject_pulses: If given, use these pulses specifically.
    :param bool autoload_pulses: Whether to employ the usepulses statement for parsing.  Requires appropriate gate definitions.
    :return: The circuit representation of the file and usepulses if
        requested. usepulses is stored in a dict under the key
        'usepulses'. It is itself a dict mapping :class:`Identifier`
        bjects to what the import, which may be the special symbol all.

    """
    with open(filename) as fd:
        return parse_jaqal_string(
            fd.read(),
            override_dict=override_dict,
            expand_macro=expand_macro,
            expand_let=expand_let,
            expand_let_map=expand_let_map,
            return_usepulses=return_usepulses,
            inject_pulses=inject_pulses,
            autoload_pulses=autoload_pulses,
            filename=filename,
        )


def parse_jaqal_string(
    jaqal,
    override_dict=None,
    expand_macro=False,
    expand_let=False,
    expand_let_map=False,
    return_usepulses=False,
    inject_pulses=None,
    autoload_pulses=True,
    filename=None,
):
    """Parse a string written in Jaqal into core types.

    :param str jaqal: The Jaqal code.
    :param override_dict:  An optional dictionary that overrides let statements in the Jaqal code.
        Note: all keys in this dictionary must exist as let statements or an error will be raised.
    :type override_dict: dict[str, float]
    :param bool expand_macro: Replace macro invocations by their body while parsing.
    :param bool expand_let: Replace let constants by their value while parsing.
    :param bool expand_let_map: Replace let constants and mapped qubits while parsing. expand_let is ignored if this is True.
    :param bool return_usepulses: Whether to both add a second return value and populate it with the usepulses statement.
    :param inject_pulses: If given, use these pulses specifically.
    :param bool autoload_pulses: Whether to employ the usepulses statement for parsing.  Requires appropriate gate definitions.
    :param str filename: The (effective) name of the Jaqal file, used for relative
        imports.
    :return: The circuit representation of the file and usepulses if
        requested. usepulses is stored in a dict under the key
        'usepulses'. It is itself a dict mapping :class:`Identifier`
        objects to what the import, which may be the special symbol all.

    """

    _monkeypatch_sly()

    sexpr, usepulses = parse_to_sexpression(jaqal, return_usepulses=True)

    circuit = build(
        sexpr,
        inject_pulses=inject_pulses,
        autoload_pulses=autoload_pulses,
        filename=filename,
    )

    if expand_macro:
        # preserve_definitions maintains old API behavior
        circuit = expand_macros(circuit, preserve_definitions=True)

    if expand_let_map:
        circuit = fill_in_let(circuit, override_dict=override_dict)
        circuit = fill_in_map(circuit)
    elif expand_let:
        circuit = fill_in_let(circuit, override_dict=override_dict)

    if sum(reg.fundamental for reg in circuit.registers.values()) > 1:
        raise JaqalError(f"Circuit has too many registers: {list(circuit.registers)}")

    if return_usepulses:
        return circuit, {"usepulses": usepulses}
    else:
        return circuit


def parse_to_sexpression(jaqal, return_usepulses=False, header_only=False):
    """Turn the input Jaqal string into an S-expression that can be fed to
    the circuit builder.

    :param str jaqal: The Jaqal code.

    :returns: A nested list of python primitives representing the circuit.

    """

    lexer = JaqalLexer()
    parser = JaqalParser(source_text=jaqal, header_only=header_only)
    try:
        parser.parse(lexer.tokenize(jaqal))
    except HeaderParsingDone:
        pass
    finally:
        sexpr = parser.top_sexpression

    if return_usepulses:
        return sexpr, parser.usepulses
    else:
        return sexpr


def parse_jaqal_file_header(filename, return_usepulses=False):
    """Parse the header of a file written in Jaqal.

    :param str filename: The name of the Jaqal file.
    :param bool return_usepulses: Whether to both add a second return value and populate it with the usepulses statement.
    :return: The circuit representation of the file's header and usepulses if
        requested. usepulses is stored in a dict under the key
        'usepulses'. It is itself a dict mapping :class:`Identifier`
        objects to what they import, which may be the special symbol all.

    """

    with open(filename, "r") as fd:
        return parse_jaqal_string_header(fd.read(), return_usepulses=return_usepulses)


def parse_jaqal_string_header(jaqal, return_usepulses=False):
    """Parse the header of a string written in Jaqal into core types.

    :param str jaqal: The Jaqal code.
    :param bool return_usepulses: Whether to both add a second return value and populate it with the usepulses statement.
    :return: The circuit representation of the file's header and usepulses if
        requested. usepulses is stored in a dict under the key
        'usepulses'. It is itself a dict mapping :class:`Identifier`
        objects to what they import, which may be the special symbol all.

    """

    res_tuple = parse_to_sexpression(
        jaqal, return_usepulses=return_usepulses, header_only=True
    )
    if return_usepulses:
        sexpr, usepulses = res_tuple
    else:
        sexpr, usepulses = res_tuple, None
    circuit = build(sexpr)

    if return_usepulses:
        return circuit, {"usepulses": usepulses}
    else:
        return circuit
