# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Extract information on the maps used in a Jaqal file."""
from collections import namedtuple

from .tree import TreeRewriteVisitor
from .identifier import Identifier
from jaqalpaq import JaqalError


def extract_map(tree):
    """Return a dictionary mapping map aliases to register ranges."""

    visitor = ExtractMapVisitor()
    visitor.visit(tree)
    return visitor.map_mapping, visitor.registers


class ExtractMapVisitor(TreeRewriteVisitor):
    def __init__(self):
        # A mapping of register identifiers to their sizes, which may still be expressed in terms of let constants.
        # This visitor only uses the names, but the sizes could be used externally to validate aliases after let
        # substitution.
        self.registers = {}
        # A mapping of map aliases to metadata about the alias. See the MapRecord type for details.
        self.map_mapping = {}

    def visit_register_statement(self, array_declaration):
        """Record information about the given register. We check that map statements are compatible with
        register statements."""
        identifier, size = self.deconstruct_array_declaration(array_declaration)
        # Although in general this is not the right place to check for register inconsistencies, the errors might
        # be too confusing if we ignored the double register declaration error.
        identifier = Identifier(self.extract_identifier(identifier))
        if identifier in self.registers:
            raise JaqalError(f"Register {identifier} already declared")
        self.registers[identifier] = size

        return self.make_register_statement(array_declaration)

    def visit_map_statement(self, target, source):
        """Create a mapping entry for this alias to the appropriate register."""
        # Even though this is always an identifier, we store it like a qualified identifier.
        dst_identifier = Identifier(self.extract_identifier(target))

        # We validate source, but store it directly as a parse tree to aid in let substitution later.

        if self.is_identifier(source):
            src_identifier = self.extract_identifier(source)
        elif self.is_array_slice(source):
            src_id_token, _ = self.deconstruct_array_slice(source)
            src_identifier = self.extract_identifier(src_id_token)
        elif self.is_array_element(source):
            src_id_token, _ = self.deconstruct_array_element(source)
            src_identifier = self.extract_identifier(src_id_token)
        else:
            raise JaqalError(f"Unknown map source format: {source}")

        if (
            src_identifier not in self.registers
            and src_identifier not in self.map_mapping
        ):
            raise JaqalError(
                f"Map statement references unknown source {src_identifier}"
            )
        if dst_identifier in self.map_mapping:
            raise JaqalError(
                f"Map statement redeclares existing alias {dst_identifier}"
            )

        self.map_mapping[dst_identifier] = source


# Each map alias is stored with a reference to the source name, its size, and the alias range (or single index). In
# general while we can resolve the source down to its register, we cannot resolve the range until let substitution.
MapRecord = namedtuple("MapRecord", ("src_name", "src_size", "alias_range"))
