from numbers import Number
from enum import Enum

from jaqal.parser import Interface, MacroContextRewriteVisitor, TreeManipulators

from jaqal.core import (
    ScheduledCircuit,
    Register,
    NamedQubit,
    GateDefinition,
    Macro,
    Parameter,
    LoopStatement,
    BlockStatement,
    Constant,
    AnnotatedValue,
)
from jaqal.qscout.native_gates import NATIVE_GATES
from jaqal.core.circuit import normalize_native_gates
from jaqal import JaqalError


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
    filename, override_dict=None, native_gates=None, processing_option=None
):
    """Parse a file written in Jaqal into core types.

    :param str filename: The name of the Jaqal file.
    :param dict[str, float] override_dict:  An optional dictionary that overrides let statements in the Jaqal code.
    Note: all keys in this dictionary must exist as let statements or an error will be raised.
    :param native_gates: If given, allow only these native gates.
    :param processing_option: What kind of processing, if any, to perform on the tree.
    :type processing_option: Option or OptionSet
    :return: A list of the gates, blocks, and loops to be run.

    """
    with open(filename) as fd:
        return parse_jaqal_string(
            fd.read(),
            override_dict=override_dict,
            native_gates=native_gates,
            processing_option=processing_option,
        )


def parse_jaqal_string(
    jaqal, override_dict=None, native_gates=None, processing_option=Option.none
):
    """Parse a string written in Jaqal into core types.

    :param str jaqal: The Jaqal code.
    :param dict[str, float] override_dict:  An optional dictionary that overrides let statements in the Jaqal code.
    Note: all keys in this dictionary must exist as let statements or an error will be raised.
    :param native_gates: If given, allow only these native gates.
    :param processing_option: What kind of processing, if any, to perform on the tree.
    :type processing_option: Option or OptionSet
    :return: A list of the gates, blocks, and loops to be run.

    """

    # The interface will automatically expand macros and scrape let, map, and register metadata.
    iface = Interface(jaqal, allow_no_usepulses=True)
    # Do some minimal processing to fill in all let and map values. The interface does not automatically do this
    # as they may rely on values from override_dict.
    let_dict = iface.make_let_dict(override_dict)
    register_dict = iface.make_register_dict(let_dict)
    tree = iface.tree
    if Option.expand_macro in processing_option:
        tree = iface.resolve_macro(tree)
    if Option.expand_let in processing_option:
        tree = iface.resolve_let(tree, let_dict=let_dict)
    if Option.expand_let_map in processing_option:
        tree = iface.resolve_map(tree)
    circuit = convert_to_circuit(tree, native_gates=native_gates)
    # Note: we also have metadata about imported files that we could output here as well.
    return circuit


def convert_to_circuit(tree, native_gates=None):
    """Convert a tree into a scheduled circuit.

    :param tree: A parse tree.
    :param native_gates: If given, allow only these native gates.
    :return: A ScheduledCircuit object that faithfully represents the input.
    """
    visitor = CoreTypesVisitor(native_gates=native_gates)
    return visitor.visit(tree)


class CoreTypesVisitor(MacroContextRewriteVisitor, TreeManipulators):
    """Define a visitor that will rewrite a Jaqal parse tree into objects from the core library.

    This class should not be used directly. Use the parse_jaqal_string,
    parse_jaqal_file, or convert_to_core_types functions instead.
    """

    def __init__(self, native_gates=None):
        super().__init__()
        self.gate_definitions = normalize_native_gates(native_gates)
        self.use_only_native_gates = native_gates is not None
        self.registers = {}  # This will also contain map aliases.
        self.macro_definitions = {}
        self.let_constants = {}

    ##
    # Visitor Methods
    #

    def visit_program(self, header_statements, body_statements):
        circuit = ScheduledCircuit(
            native_gates=NATIVE_GATES if self.use_only_native_gates else None
        )
        for stmt in body_statements:
            circuit.body.append(stmt)
        circuit.registers.update(self.registers)
        circuit.macros.update(self.macro_definitions)
        circuit.constants.update(self.let_constants)
        if not self.use_only_native_gates:
            circuit.native_gates.update(self.gate_definitions)
        return circuit

    def visit_register_statement(self, array_declaration):
        identifier_token, size_tree = self.deconstruct_array_declaration(
            array_declaration
        )
        name = str(self.extract_identifier(identifier_token))
        if name in self.registers:
            raise JaqalError(f"Redefinition of register {name}")
        if self.is_integer(size_tree):
            size = self.extract_integer(size_tree)
        elif self.is_let_identifier(size_tree):
            assert not self.in_macro, "Someone created an invalid parse tree"
            size_var_name = str(self.deconstruct_let_identifier(size_tree))
            size = self.resolve_scalar_identifier(size_var_name)
        else:
            raise JaqalError(f"Unknown object used as register size: {size_tree}")
        reg = Register(name, size)
        self.registers[name] = reg

    def visit_macro_definition(self, name, arguments, block):
        """Process a macro definition, storing the definition and removing it from the
        body statements."""

        name = str(self.extract_identifier(name))
        parameters = [
            Parameter(str(self.extract_identifier(arg)), None) for arg in arguments
        ]
        block = self.deconstruct_macro_gate_block(block)

        self.macro_definitions[name] = Macro(name, parameters, block)

        return None

    def visit_let_statement(self, identifier, number):
        """Process a let statement by storing the definition and removing it from the header
        statements."""
        name = str(self.extract_identifier(identifier))
        value = self.extract_signed_number(number)
        int_value = int(value)
        if value == int_value:
            value = int_value

        self.let_constants[name] = Constant(name, value)

        return None

    def visit_map_statement(self, target, source):
        """Process a map statement by storing its definition and removing it from the header
        statements."""
        # Target is the map being defined. source is the register or map we are basing it on.
        tgt_name = str(self.extract_identifier(target))
        if tgt_name in self.registers:
            raise JaqalError(f"Redefinition of map or register {tgt_name}")

        if self.is_array_slice(source):
            src_name, src_slice = self.deconstruct_array_slice(source)
            src_name = str(self.extract_identifier(src_name))
            if src_name not in self.registers:
                raise JaqalError(
                    f"map {tgt_name} based on non-existent source {src_name}"
                )
            src_reg = self.registers[src_name]
            src_start, src_stop, src_step = src_slice
            src_start = self.resolve_slice_element(src_start, lambda: 0)

            def get_default_stop():
                try:
                    return src_reg.size
                except JaqalError as exc:
                    raise JaqalError(f"Cannot determine size of {src_name}: {exc}")

            src_stop = self.resolve_slice_element(src_stop, get_default_stop)
            src_step = self.resolve_slice_element(src_step, lambda: 1)
            src_slice = slice(src_start, src_stop, src_step)
            self.registers[tgt_name] = Register(
                tgt_name, alias_from=src_reg, alias_slice=src_slice
            )
        elif self.is_array_element(source):
            src_name, src_index = self.deconstruct_array_element(source)
            src_name = str(self.extract_identifier(src_name))
            if src_name not in self.registers:
                raise JaqalError(
                    f"map {tgt_name} based on non-existent source {src_name}"
                )
            src_reg = self.registers[src_name]
            src_index = self.extract_signed_integer(src_index)
            self.registers[tgt_name] = NamedQubit(
                tgt_name, alias_from=src_reg, alias_index=src_index
            )
        elif self.is_identifier(source):
            # Basically renaming a whole register.
            src_name = str(self.extract_identifier(source))
            if src_name not in self.registers:
                raise JaqalError(
                    f"map {tgt_name} based on non-existent source {src_name}"
                )
            src_reg = self.registers[src_name]
            self.registers[tgt_name] = Register(tgt_name, alias_from=src_reg)

        return None

    def resolve_slice_element(self, element, default_func):
        if element is None:
            return default_func()
        if self.is_signed_integer(element):
            return self.extract_signed_integer(element)
        if self.is_let_identifier(element):
            id_name = str(self.deconstruct_let_identifier(element))
            return self.resolve_scalar_identifier(id_name)

    def visit_parallel_gate_block(self, statements):
        return BlockStatement(parallel=True, statements=statements)

    def visit_sequential_gate_block(self, statements):
        return BlockStatement(parallel=False, statements=statements)

    def visit_loop_statement(self, repetition_count, block):
        repetition_count = self.extract_integer(repetition_count)
        return LoopStatement(iterations=repetition_count, statements=block)

    def visit_gate_statement(self, gate_name, gate_args):
        gate_name = str(self.extract_qualified_identifier(gate_name))
        gate_args = [self.convert_gate_arg(arg) for arg in gate_args]
        gate_def = self.get_gate_definition(gate_name, gate_args)
        gate = gate_def(*gate_args)
        return gate

    def visit_array_element_qual(self, identifier, index):
        if self.is_signed_integer(index):
            index = int(index)
        elif self.is_let_identifier(index):
            index_name = str(self.deconstruct_let_identifier(index))
            index = self.resolve_scalar_identifier(index_name)
        else:
            raise JaqalError(f"Unknown index type {index}")
        identifier = self.extract_qualified_identifier(identifier)
        ident_str = str(identifier)
        if ident_str not in self.registers:
            raise JaqalError(f"No register or map named {ident_str}")
        reg = self.registers[str(identifier)][index]
        return reg

    ##
    # Helper Methods
    #

    def convert_gate_arg(self, arg):
        """Take a gate argument that may still be a parse tree and return
        a type that can be passed to the GateStatement constructor."""

        if self.is_signed_number(arg):
            return float(arg)
        elif isinstance(arg, NamedQubit):
            return arg
        elif self.is_let_or_map_identifier(arg):
            name = str(self.deconstruct_let_or_map_identifier(arg))
            return self.resolve_scalar_identifier(name, can_be_qubit=True)
        else:
            raise TypeError(f"Unrecognized gate argument {arg}")

    def get_gate_definition(self, gate_name, gate_args):
        """Look up or create a gate definition for a gate with the
        given name and arguments."""
        if gate_name in self.gate_definitions:
            return self.gate_definitions[gate_name]
        elif not self.use_only_native_gates:
            params = [
                self.make_parameter_from_argument(index, arg)
                for index, arg in enumerate(gate_args)
            ]
            gate_def = GateDefinition(gate_name, params)
            self.gate_definitions[gate_name] = gate_def
            return gate_def
        else:
            raise JaqalError(f"Gate {gate_name} not a QSCOUT native gate")

    @staticmethod
    def make_parameter_from_argument(index, arg):
        """Create a Parameter object with a default name and a type appropriate
        to the given argument."""
        name = f"{index}"
        if isinstance(arg, Number):
            kind = "float"
        elif isinstance(arg, NamedQubit):
            kind = "qubit"
        elif isinstance(arg, AnnotatedValue):
            # This is either an unresolved macro parameter or unresolved let constant.
            # Either way we treat it the same.
            kind = arg.kind
        else:
            raise TypeError("Unrecognized argument type to gate")
        return Parameter(name, kind)

    def resolve_scalar_identifier(self, name, can_be_qubit=False):
        """Figure out if an identifier is a mapped single qubit, a macro parameter, or let constant."""
        if self.in_macro:
            if any(str(arg) == name for arg in self.macro_args):
                return Parameter(name, None)
        if can_be_qubit and name in self.registers:
            named_qubit = self.registers[name]
            if not isinstance(named_qubit, NamedQubit):
                raise ValueError(f"Scalar variable {name} is a register")
            return named_qubit
        if name in self.let_constants:
            return self.let_constants[name]
        raise JaqalError(f"Unknown variable {name}")
