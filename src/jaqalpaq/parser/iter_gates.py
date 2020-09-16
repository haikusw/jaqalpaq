# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Functions for iterating over gates in a Jaqal file"""

from .tree import ParseTreeVisitor
from .identifier import Identifier
from jaqalpaq import JaqalError


def get_gates_and_loops(tree):
    """Return a list of Gate and Loop objects. This assumes many stages of simplification have already happened to
    the tree and may fail if there are unresolved symbols."""
    visitor = IterateGatesAndLoopsVisitor()
    return visitor.visit(tree)


class IterateGatesAndLoopsVisitor(ParseTreeVisitor):
    """Parse tree visitor that takes a simplified Jaqal parse tree and returns a list of JaqalObject's."""

    def visit_program(self, header_statements, body_statements):
        return body_statements

    def visit_register_statement(self, array_declaration):
        return None

    def visit_map_statement(self, target, source):
        raise JaqalError(f"Map statements should have been removed by now")

    def visit_let_statement(self, identifier, number):
        raise JaqalError(f"Let statements should have been removed by now")

    def visit_usepulses_statement(self, identifier, objects):
        return None

    def visit_gate_statement(self, gate_name, gate_args):
        return Gate(gate_name, gate_args)

    def visit_macro_definition(self, name, arguments, block):
        raise JaqalError(f"Macro definition should have been removed by now")

    def visit_loop_statement(self, repetition_count, block):
        return Loop(repetition_count, block)

    def visit_sequential_gate_block(self, statements):
        return SequentialGateBlock(statements)

    def visit_parallel_gate_block(self, statements):
        return ParallelGateBlock(statements)

    def visit_array_declaration(self, identifier, size):
        return None

    def visit_array_element(self, identifier, index):
        return (identifier, index)

    def visit_array_element_qual(self, identifier, index):
        return (identifier, index)

    def visit_array_slice(self, identifier, index_slice):
        return None

    def visit_let_identifier(self, identifier):
        return identifier

    def visit_let_or_map_identifier(self, identifier):
        return identifier

    def visit_qualified_identifier(self, names):
        return str(Identifier(names))

    def visit_identifier(self, identifier_string):
        return identifier_string


# Define the objects we return when iterating over gates. Having the `is_*` methods really just allows us
# to check the type without having to import the classes into the user's namespace. I'm not sure if it's a
# good idea but it seems like one.


class JaqalObject:
    """Base class for objects to be returned from parsing Jaqal."""

    # Class-level variables to be selectively overridden by derived classes.
    is_gate = False
    is_loop = False
    is_parallel_gate_block = False
    is_sequential_gate_block = False

    @property
    def is_gate_block(self):
        return self.is_parallel_gate_block or self.is_sequential_gate_block


class Gate(JaqalObject):

    is_gate = True

    def __init__(self, gate_name, gate_args):
        # gate_args are either numbers or (register_name, index) tuples.
        self.gate_name = gate_name
        self.gate_args = gate_args

    def __eq__(self, other):
        return self.gate_name == other.gate_name and self.gate_args == other.gate_args

    def __repr__(self):
        return f"Gate({self.gate_name}, {self.gate_args})"


class Loop(JaqalObject):

    is_loop = True

    def __init__(self, repetition_count, block):
        self.repetition_count = repetition_count
        self.block = block

    def __eq__(self, other):
        return (
            self.repetition_count == other.repetition_count
            and self.block == other.block
        )

    def __repr__(self):
        return f"Loop({self.repetition_count}, {self.block})"


class ParallelGateBlock(JaqalObject):

    is_parallel_gate_block = True

    def __init__(self, gates):
        self.gates = gates

    def __eq__(self, other):
        return self.gates == other.gates

    def __repr__(self):
        return f"ParallelGateBlock({self.gates})"


class SequentialGateBlock(JaqalObject):

    is_sequential_gate_block = True

    def __init__(self, gates):
        self.gates = gates

    def __eq__(self, other):
        return self.gates == other.gates

    def __repr__(self):
        return f"SequentialGateBlock({self.gates})"
