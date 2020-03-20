from numbers import Number

from jaqal import Interface, TreeRewriteVisitor, TreeManipulators

from jaqalpup.core import (
    ScheduledCircuit, Register, NamedQubit, GateDefinition,
    Parameter, LoopStatement, BlockStatement, NATIVE_GATES
)
from jaqalpup import QSCOUTError


def parse_jaqal_file(filename, override_dict=None, use_qscout_native_gates=False):
    """Parse a file written in Jaqal into core types.

    filename -- The name of the Jaqal file.

    override_dict -- An optional dictionary of string: number mappings that overrides let statements in the Jaqal code.
    Note: all keys in this dictionary must exist as let statements or an error will be raised.
    """
    with open(filename) as fd:
        return parse_jaqal_string(fd.read(), override_dict=override_dict,
                                  use_qscout_native_gates=use_qscout_native_gates)


def parse_jaqal_string(jaqal, override_dict=None, use_qscout_native_gates=False):
    """Parse a string written in Jaqal into core types.

    jaqal -- The Jaqal code as a string.

    override_dict -- An optional dictionary of string: number mappings that overrides let statements in the Jaqal code.
    Note: all keys in this dictionary must exist as let statements or an error will be raised.
    """

    # The interface will automatically expand macros and scrape let, map, and register metadata.
    iface = Interface(jaqal, allow_no_usepulses=True)
    # Do some minimal processing to fill in all let and map values. The interface does not automatically do this
    # as they may rely on values from override_dict.
    let_dict = iface.make_let_dict(override_dict)
    tree = iface.resolve_let(let_dict=let_dict)
    tree = iface.resolve_map(tree)
    visitor = CoreTypesVisitor(iface.make_register_dict(let_dict),
                               use_qscout_native_gates=use_qscout_native_gates)
    circuit = visitor.visit(tree)
    # Note: we also have metadata about register sizes and imported files that we could output here as well.
    return circuit


class CoreTypesVisitor(TreeRewriteVisitor, TreeManipulators):
    """Define a visitor that will rewrite a Jaqal parse tree into objects from the core library."""

    def __init__(self, register_dict, use_qscout_native_gates=False):
        super().__init__()
        self.registers = {name: Register(name, size) for name, size in register_dict.items()}
        if use_qscout_native_gates:
            self.gate_definitions = {gate.name: gate for gate in NATIVE_GATES}
        else:
            self.gate_definitions = {}
        self.use_qscout_native_gates = bool(use_qscout_native_gates)

    ##
    # Visitor Methods
    #

    def visit_program(self, header_statements, body_statements):
        circuit = ScheduledCircuit(qscout_native_gates=self.use_qscout_native_gates)
        for stmt in body_statements:
            circuit.body.append(stmt)
        circuit.registers.update(self.registers)
        if not self.use_qscout_native_gates:
            circuit.native_gates.update(self.gate_definitions)
        return circuit

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
        index = int(index)
        identifier = self.extract_qualified_identifier(identifier)
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
        else:
            raise TypeError(f"Unrecognized gate argument {arg}")

    def get_gate_definition(self, gate_name, gate_args):
        """Look up or create a gate definition for a gate with the
        given name and arguments."""
        if gate_name in self.gate_definitions:
            return self.gate_definitions[gate_name]
        elif not self.use_qscout_native_gates:
            params = [self.make_parameter_from_argument(index, arg)
                      for index, arg in enumerate(gate_args)]
            gate_def = GateDefinition(gate_name, params)
            self.gate_definitions[gate_name] = gate_def
            return gate_def
        else:
            raise QSCOUTError(f"Gate {gate_name} not a QSCOUT native gate")

    @staticmethod
    def make_parameter_from_argument(index, arg):
        """Create a Parameter object with a default name and a type appropriate
        to the given argument."""
        name = f"{index}"
        if isinstance(arg, Number):
            kind = 'float'
        elif isinstance(arg, NamedQubit):
            kind = 'qubit'
        else:
            raise TypeError("Unrecognized argument type to gate")
        return Parameter(name, kind)
