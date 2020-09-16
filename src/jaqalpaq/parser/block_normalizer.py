# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import itertools

from .tree import TreeRewriteVisitor
from jaqalpaq import JaqalError


def normalize_blocks_with_unitary_timing(tree):
    """Simplify all gate blocks under the assumption that all gates take the same amount of time. All blocks are
    transformed into sequential blocks of parallel blocks. No parallel blocks have nested blocks. This step assumes
    macro expansion has already occurred. Loops are allowed but must be at top level."""

    visitor = UnitaryBlockRewriteVisitor()
    new_tree = visitor.visit(tree)
    return new_tree


class UnitaryBlockRewriteVisitor(TreeRewriteVisitor):
    """Visitor to rewrite a tree as a sequence of gates or serial blocks, each sequential block containing gates and
    parallel blocks, with no further nesting. To accomplish this, we assume all gates have the same timing. No
    validation of whether the hardware can actually run these gates in parallel is performed."""

    def visit_program(self, header_statements, body_statements):
        body_statements = self._expand_sequential_gate_blocks(body_statements)
        return self.make_program(header_statements, body_statements)

    def visit_sequential_gate_block(self, statements):
        """Inline any sequential block gates (which must have been manufactured in this visitor)."""
        ret_statements = self._expand_sequential_gate_blocks(statements)

        return self.make_sequential_gate_block(ret_statements)

    def visit_parallel_gate_block(self, statements):
        """Convert a parallel gate block into a serial gate block with possible parallel gate blocks. The interior
        parallel gate blocks have no further nesting."""
        # gate_sequences is a list of lists of lists
        gate_sequences = [_sequence_gates(stmt) for stmt in statements]

        sequential_statements = []

        # The expansion inside the call to zip_longest breaks the first list
        for par_tuple in itertools.zip_longest(*gate_sequences):
            gate_lists = [gl for gl in par_tuple if gl is not None]
            # This breaks the second list so all we have is a list of gates. These are all the gates that may be
            # executed in parallel at the given timestep.
            gates = list(itertools.chain(*gate_lists))
            if not all(self.is_gate_statement(gate) for gate in gates):
                raise JaqalError(f"Expected list of parallel gates, found {gates}")
            assert gates, "No gates were returned instead of stopping the iteration"
            if len(gates) == 1:
                sequential_statements.append(gates[0])
            else:
                sequential_statements.append(self.make_parallel_gate_block(gates))

        # By converting a parallel gate block into a sequential one, we might end up nesting sequential blocks
        # inside each other. We will iron this out later.
        return self.make_sequential_gate_block(sequential_statements)

    def _expand_sequential_gate_blocks(self, statements):
        ret_statements = []

        for statement in statements:
            if self.is_sequential_gate_block(statement):
                ret_statements.extend(self.deconstruct_sequential_gate_block(statement))
            else:
                ret_statements.append(statement)

        return ret_statements


def _sequence_gates(tree):
    """Given either a gate or sequential gate block, return a list of lists of gates, each inner list representing
    all the gates run at once (a parallel block). See GateSequencingVisitor for more details."""

    gates = GateSequencingVisitor().visit(tree)

    if not isinstance(gates, list):
        raise JaqalError(
            f"Expected list returned from GateSequencingVisitor, found {gates}"
        )

    if not gates or isinstance(gates[0], list):
        # The visitor already formatted us into a list of lists.
        return gates
    else:
        # We reached one of the cases where the visitor could not format us into a list, so we need to wrap the result.
        return [gates]


class GateSequencingVisitor(TreeRewriteVisitor):
    """A visitor that helps the UnitaryBlockRewriteVisitor by sequencing gates into lists of lists of gates.
    This visitor assumes that it receives either a single gate, or a sequential block containing parallel blocks and
    gates. Additionally, a parallel block must have only gates inside (no nested sequential blocks)."""

    def visit_sequential_gate_block(self, statements):
        return statements

    def visit_parallel_gate_block(self, statements):
        if not all(
            isinstance(stmt, list) and self.is_gate_statement(stmt[0])
            for stmt in statements
        ):
            raise JaqalError("Non gate statement found in parallel block")
        return [lst[0] for lst in statements]

    def visit_gate_statement(self, gate_name, gate_args):
        return [self.make_gate_statement(gate_name, gate_args)]
