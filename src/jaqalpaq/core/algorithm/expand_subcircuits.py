"""Expand all subcircuits in place in a Circuit."""

from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core.circuit import Circuit
from jaqalpaq.core.block import BlockStatement, LoopStatement
from jaqalpaq.core.gatedef import GateDefinition


def expand_subcircuits(circuit, prepare_def=None, measure_def=None):
    """Expand subcircuit blocks by adding a prepare and measure gate as
    the first and last gates in the sequential block.

    :param Circuit circuit: The circuit in which to expand subcircuits.

    :param str or GateDefinition prepare_def: The definition of the
        gate to place in the beginning of each subcircuit. If a string is
        provided, look up in the circuit's native gates. If not given,
        create a new definition using this string or 'prepare_all'.

    :param str or GateDefinition measure_def: The definition of the
        gate to place at the end of each subcircuit. If a string is
        provided, look up in the circuit's native gates. If not given,
        create a new definition using this string or 'measure_all'.

    """

    prepare_def = _choose_bounding_gate(prepare_def, "prepare_all", circuit)
    measure_def = _choose_bounding_gate(measure_def, "measure_all", circuit)

    visitor = SubcircuitExpander(prepare_def, measure_def)
    return visitor.visit(circuit)


def _choose_bounding_gate(user_def, default_name, circuit):
    """Choose a gate definition from either the one provided by the user,
    one available in circuit, or a default one created on the spot."""

    if not isinstance(user_def, str) and user_def is not None:
        return user_def

    if isinstance(user_def, str):
        name = user_def
    else:
        name = default_name

    try:
        return circuit.native_gates[name]
    except KeyError:
        pass

    return GateDefinition(name)


class SubcircuitExpander(Visitor):
    def __init__(self, prepare_def, measure_def):
        self.prepare_def = prepare_def
        self.measure_def = measure_def

    def visit_default(self, obj):
        """By default we leave all objects alone. Note that the object is not copied."""
        return obj

    def visit_Circuit(self, circuit):
        new_circuit = Circuit(native_gates=circuit.native_gates)
        new_circuit.macros.update(circuit.macros)
        new_circuit.constants.update(circuit.constants)
        new_circuit.registers.update(circuit.registers)
        new_circuit.body.statements.extend(self.visit(circuit.body).statements)
        return new_circuit

    def visit_LoopStatement(self, loop):
        return LoopStatement(loop.iterations, self.visit(loop.statements))

    def visit_BlockStatement(self, block):
        if block.subcircuit:
            return self.process_subcircuit(block)
        else:
            return self.process_non_subcircuit_block(block)

    def process_subcircuit(self, block):
        statements = [
            self.prepare_def(),
            *(self.visit(stmt) for stmt in block.statements),
            self.measure_def(),
        ]
        return BlockStatement(parallel=block.parallel, statements=statements)

    def process_non_subcircuit_block(self, block):
        statements = [self.visit(stmt) for stmt in block.statements]
        return BlockStatement(parallel=block.parallel, statements=statements)
