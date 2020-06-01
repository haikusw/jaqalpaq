from enum import Enum

from .interface import Interface
from .macro_context_visitor import MacroContextRewriteVisitor
from .tree import TreeManipulators

from jaqalpaq.core.circuitbuilder import build
from jaqalpaq import JaqalError


class Option(Enum):
    """Control how and whether the parser expands certain constructs."""

    none = 0
    expand_macro = 0x1
    expand_let = 0x2
    expand_let_map = 0x6
    full = 0xF

    def __contains__(self, item):
        return (self.value & item.value) == item.value

    def __or__(self, other):
        if isinstance(other, OptionSet):
            result = OptionSet([self]) | other
        else:
            result = OptionSet([self, other])
        return result

    def __ror__(self, other):
        return self | other


class OptionSet(set):
    """Represent multiple parser options. Acts like a bitmask"""

    def __contains__(self, other):
        return any(other in item for item in self)


def parse_jaqal_file(
    filename,
    override_dict=None,
    native_gates=None,
    processing_option=Option.none,
    return_usepulses=False,
):
    """Parse a file written in Jaqal into core types.

    :param str filename: The name of the Jaqal file.
    :param dict[str, float] override_dict:  An optional dictionary that overrides let statements in the Jaqal code.
    Note: all keys in this dictionary must exist as let statements or an error will be raised.
    :param native_gates: If given, allow only these native gates.
    :param processing_option: What kind of processing, if any, to perform on the tree.
    :type processing_option: Option or OptionSet
    :param bool return_usepulses: Whether to both add a second return value and populate it with the usepulses statement.
    :return: A list of the gates, blocks, and loops to be run.

    """
    with open(filename) as fd:
        return parse_jaqal_string(
            fd.read(),
            override_dict=override_dict,
            native_gates=native_gates,
            processing_option=processing_option,
            return_usepulses=return_usepulses,
        )


def parse_jaqal_string(
    jaqal,
    override_dict=None,
    native_gates=None,
    processing_option=Option.none,
    return_usepulses=False,
):
    """Parse a string written in Jaqal into core types.

    :param str jaqal: The Jaqal code.
    :param dict[str, float] override_dict:  An optional dictionary that overrides let statements in the Jaqal code.
    Note: all keys in this dictionary must exist as let statements or an error will be raised.
    :param native_gates: If given, allow only these native gates.
    :param processing_option: What kind of processing, if any, to perform on the tree.
    :type processing_option: Option or OptionSet
    :param bool return_usepulses: Whether to both add a second return value and populate it with the usepulses statement.
    :return: A list of the gates, blocks, and loops to be run.

    """

    # The interface will automatically expand macros and scrape let, map, and register metadata.
    iface = Interface(jaqal, allow_no_usepulses=True)
    # Do some minimal processing to fill in all let and map values. The interface does not automatically do this
    # as they may rely on values from override_dict.
    let_dict = iface.make_let_dict(override_dict)
    tree = iface.tree
    if Option.expand_macro in processing_option:
        tree = iface.resolve_macro(tree)
    if Option.expand_let in processing_option:
        tree = iface.resolve_let(tree, let_dict=let_dict)
    if Option.expand_let_map in processing_option:
        tree = iface.resolve_map(tree)
    circuit = convert_to_circuit(tree, native_gates=native_gates)

    if return_usepulses:
        ret_extra = {"usepulses": iface.usepulses}
        ret_value = (circuit, ret_extra)
    else:
        ret_value = circuit

    if sum(reg.fundamental for reg in circuit.registers.values()) > 1:
        raise JaqalError(f"Circuit has too many registers: {list(circuit.registers)}")

    return ret_value


def convert_to_circuit(tree, native_gates=None):
    """Convert a tree into a scheduled circuit.

    :param tree: A parse tree.
    :param native_gates: If given, allow only these native gates.
    :return: A ScheduledCircuit object that faithfully represents the input.
    """
    visitor = CoreTypesVisitor(native_gates=native_gates)
    return visitor.visit(tree)


class CoreTypesVisitor(MacroContextRewriteVisitor, TreeManipulators):
    def __init__(self, native_gates=None):
        super().__init__()
        self.native_gates = native_gates

    def visit_program(self, header_statements, body_statements):
        circuit_sexpr = ("circuit", *header_statements, *body_statements)
        return build(circuit_sexpr, native_gates=self.native_gates)

    def visit_usepulses_statement(self, identifier, objects):
        """Ignore a usepulses statement."""
        return None

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
