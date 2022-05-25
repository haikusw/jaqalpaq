# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Normalize gates in blocks under the assumption that they all have
unitary timing (or are padded to be so)."""

from itertools import zip_longest

from jaqalpaq.error import JaqalError
from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core.circuit import Circuit
from jaqalpaq.core.block import BlockStatement, LoopStatement


def normalize_blocks_with_unitary_timing(circuit):
    """Normalize the given circuit to contain only parallel blocks. This
    is possible by assuming that all gates run in parallel run in one unit
    of time.

    This does not expand loops, macros, lets, or maps.

    :param Circuit circuit: The circuit to normalize.

    :returns: A new, normalized circuit. Although the circuit will be new, it may share
        structure with the input circuit, thus the input should not be changed.
    :rtype: Circuit

    """

    visitor = BlockNormalizer()
    return visitor.visit(circuit)


class BlockNormalizer(Visitor):
    def visit_default(self, obj):
        """By default we leave all objects alone. Note that the object is not
        copied."""
        return obj

    def visit_Circuit(self, circuit):
        """Return a new Circuit with the same metadata and normalized
        gates."""

        new_circuit = Circuit(native_gates=circuit.native_gates)
        new_circuit.constants.update(circuit.constants)
        new_circuit.macros.update(circuit.macros)
        new_circuit.registers.update(circuit.registers)
        new_circuit.body.statements.extend(self.visit(circuit.body).statements)
        return new_circuit

    def visit_BlockStatement(self, obj: BlockStatement):
        """Normalize a block by first normalizing every statement or block
        inside it, If this is a parallel block, it is converted to a
        serial block with one or more serial blocks. If it is a serial
        block, it is passed up with its normalized statements and any
        subblocks that are sequential expanded.

        """

        visited_statements = [self.visit(stmt) for stmt in obj.statements]

        if obj.parallel:
            new_statements = []
            for parallel_chunk in self.iter_chunk_blocks(visited_statements):
                if len(parallel_chunk) == 1:
                    (block,) = parallel_chunk
                else:
                    block = BlockStatement(parallel=True, statements=parallel_chunk)
                new_statements.append(block)
        else:
            new_statements = list(self.iter_unroll_blocks(visited_statements))
        new_block = BlockStatement(statements=new_statements)
        return new_block

    def iter_chunk_blocks(self, statements):
        """Iterate over statements in a parallel block and return chunks
        consisting of the next statement from within each of those blocks
        (treating a gate as a block of 1 statement)."""
        iterators = [UnrollIterator().visit(stmt) for stmt in statements]
        for ch in zip_longest(*iterators):
            non_none = list(filter(lambda x: x is not None, ch))
            chunk = []
            for stmt in non_none:
                if isinstance(stmt, BlockStatement):
                    assert stmt.parallel, "Normalization Failed"
                    chunk.extend(stmt.statements)
                else:
                    chunk.append(stmt)
                if isinstance(stmt, LoopStatement):
                    raise JaqalError(
                        "A Loop is embedded somewhere within a parallel block. This is legal Jaqal, but cannot be handled here. Unroll loops first."
                    )

            yield chunk

    def iter_unroll_blocks(self, statements):
        for stmt in statements:
            yield from UnrollIterator().visit(stmt)


class UnrollIterator(Visitor):
    """Unroll a block or single gate into a sequence of gates. The
    resulting sequence will have no sequential blocks but perhaps
    parallel blocks.

    """

    def visit_default(self, obj):
        yield obj

    def visit_BlockStatement(self, obj):
        if obj.parallel:
            # This is ok in iter_unroll_blocks but would be an error
            # in iter_chunk_blocks.
            yield obj
        else:
            for stmt in obj.statements:
                yield stmt
