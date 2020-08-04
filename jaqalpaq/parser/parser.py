# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from .interface import Interface
from .macro_context_visitor import MacroContextRewriteVisitor
from .tree import TreeManipulators

from jaqalpaq.core.circuitbuilder import build
from jaqalpaq import JaqalError


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
    :return: The circuit representation of the file and usepulses if
        requested. usepulses is stored in a dict under the key
        'usepulses'. It is itself a dict mapping :class:`Identifier`
        objects to what the import, which may be the special symbol all.

    """

    # The interface will automatically expand macros and scrape let, map, and register metadata.
    iface = Interface(jaqal, allow_no_usepulses=True)
    # Do some minimal processing to fill in all let and map values. The interface does not
    # automatically do this as they may rely on values from override_dict.
    let_dict = iface.make_let_dict(override_dict)
    tree = iface.tree
    expand_let = expand_let or expand_let_map
    if expand_macro:
        tree = iface.resolve_macro(tree)
    if expand_let:
        tree = iface.resolve_let(tree, let_dict=let_dict)
    if expand_let_map:
        tree = iface.resolve_map(tree)
    circuit = convert_to_circuit(
        tree, inject_pulses=inject_pulses, autoload_pulses=autoload_pulses
    )

    if return_usepulses:
        ret_extra = {"usepulses": iface.usepulses}
        ret_value = (circuit, ret_extra)
    else:
        ret_value = circuit

    if sum(reg.fundamental for reg in circuit.registers.values()) > 1:
        raise JaqalError(f"Circuit has too many registers: {list(circuit.registers)}")

    return ret_value


def convert_to_circuit(tree, inject_pulses=None, autoload_pulses=False):
    """Convert a tree into a scheduled circuit.

    :param tree: A parse tree.
    :param inject_pulses: If given, use these pulses specifically.
    :param bool autoload_pulses: Whether to employ the usepulses statement for parsing.  Requires appropriate gate definitions.
    :return: A Circuit object that faithfully represents the input.
    """
    visitor = CoreTypesVisitor(
        inject_pulses=inject_pulses, autoload_pulses=autoload_pulses
    )
    return visitor.visit(tree)


class CoreTypesVisitor(MacroContextRewriteVisitor, TreeManipulators):
    def __init__(self, inject_pulses=None, autoload_pulses=False):
        super().__init__()
        self.inject_pulses = inject_pulses
        self.autoload_pulses = autoload_pulses

    def visit_program(self, header_statements, body_statements):
        circuit_sexpr = ("circuit", *header_statements, *body_statements)
        return build(
            circuit_sexpr,
            inject_pulses=self.inject_pulses,
            autoload_pulses=self.autoload_pulses,
        )

    def visit_usepulses_statement(self, identifier, objects):
        return ("usepulses", identifier, objects)

    def visit_register_statement(self, array_declaration):
        if self.in_macro:
            raise JaqalError("Someone created an invalid parse tree")
        name, size = self.deconstruct_array_declaration(array_declaration)
        sexpr = ("register", name, size)
        return sexpr

    def visit_macro_definition(self, name, arguments, block):
        # As an artifact of the way the parse tree is rebuilt, the block ends up
        # being a parse tree with a single statement which is the s-expression block.
        return ("macro", name, *arguments, block)

    def visit_macro_gate_block(self, block):
        # The macro gate block level is helpful in setting macro contexts but otherwise
        # superfluous. We have to call the superclass for macro tracking.
        super().visit_macro_gate_block(block)
        return block

    def visit_let_statement(self, identifier, number):
        sexpr = ("let", identifier, number)
        return sexpr

    def visit_map_statement(self, target, source):
        if self.is_array_slice(source):
            src_name, src_slice_tuple = self.deconstruct_array_slice(source)
            sexpr = ("map", target, src_name, *src_slice_tuple)
        elif self.is_array_element(source):
            src_name, src_index = self.deconstruct_array_element(source)
            sexpr = ("map", target, src_name, src_index)
        else:
            sexpr = ("map", target, source)

        return sexpr

    def visit_parallel_gate_block(self, statements):
        return ("parallel_block", *statements)

    def visit_sequential_gate_block(self, statements):
        return ("sequential_block", *statements)

    def visit_loop_statement(self, repetition_count, block):
        sexpr = ("loop", repetition_count, block)
        return sexpr

    def visit_gate_statement(self, gate_name, gate_args):
        return ("gate", gate_name, *gate_args)

    def visit_array_element_qual(self, identifier, index):
        sexpr = ("array_item", identifier, index)
        return sexpr

    ##
    # Reading parts of statements
    #

    def visit_let_identifier(self, identifier):
        return identifier

    def visit_let_or_map_identifier(self, identifier):
        return identifier

    ##
    # Reading tokens
    #

    def visit_identifier(self, token):
        return str(self.extract_identifier(token))

    def visit_qualified_identifier(self, names):
        return ".".join(names)

    def visit_integer(self, token):
        return self.extract_integer(token)

    def visit_signed_integer(self, token):
        return self.extract_signed_integer(token)

    def visit_signed_number(self, token):
        return self.extract_signed_number(token)

    def visit_number(self, token):
        return self.extract_number(token)
