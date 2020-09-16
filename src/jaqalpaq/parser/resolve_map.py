# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Resolve references to mapped arrays down to registers."""
from sys import maxsize

from .macro_context_visitor import MacroContextRewriteVisitor
from jaqalpaq import JaqalError


def resolve_map(tree, map_dict, register_set):
    """Replace all mapped aliases with references to the underlying register. This cannot handle references to
    full mapped arrays, which may occur in macro arguments, but only references to individual elements."""

    visitor = ResolveMapVisitor(map_dict, register_set)
    resolved = visitor.visit(tree)
    return resolved


class ResolveMapVisitor(MacroContextRewriteVisitor):
    def __init__(self, map_dict, register_set):
        super().__init__()
        if any(reg in map_dict for reg in register_set):
            raise JaqalError("Name of a map alias is also a register")
        self.map_dict = map_dict
        self.register_set = register_set

    def visit_array_element_qual(self, identifier, index):
        """Validate the index is an integer."""
        identifier_value = self.extract_qualified_identifier(identifier)
        index_value = self.extract_signed_integer(index)

        if self.is_macro_argument(identifier_value):
            raise JaqalError(
                "This macro uses an argument as a register; please resolve macros before resolving maps"
            )

        identifier_value, index_value = self.resolve_map_element(
            identifier_value, index_value
        )
        identifier = self.make_qualified_identifier(identifier_value)
        index = self.make_signed_integer(index_value)

        return self.make_array_element_qual(identifier, index)

    def visit_gate_statement(self, gate_name, gate_args):
        """We have to treat plain identifiers differently than array element accesses, but there's no easy way
        to differentiate, so we catch the array elements in the visit_array_element method and the bare
        qubit references here."""

        gate_args = [self.map_gate_arg(arg) for arg in gate_args]
        return self.make_gate_statement(gate_name, gate_args)

    def map_gate_arg(self, arg):
        """Given an argument to a gate, either resolve any mappings or return the original argument unchanged."""
        if self.is_let_or_map_identifier(arg):
            identifier = self.deconstruct_let_or_map_identifier(arg)
            if self.is_macro_argument(identifier):
                return arg
            return self.resolve_map_identifier(identifier)
        else:
            return arg

    def is_macro_argument(self, identifier):
        """Return whether we are in a macro definition and if so if this identifier is the same as one of the
        macro arguments."""
        return self.in_macro and identifier in self.macro_args

    def resolve_map_element(self, identifier_value, index_value):
        """Repeatedly resolve this map element until reaching a register."""
        while identifier_value in self.map_dict:
            identifier_value, index_value = self.resolve_map_element_single(
                identifier_value, index_value
            )
        return identifier_value, index_value

    def resolve_map_element_single(self, identifier_value, index_value):
        """Find the array or register that this identifier maps to, and return the name and index."""

        if identifier_value not in self.map_dict:
            raise JaqalError(f"Cannot resolve map {identifier_value}")

        source = self.map_dict[identifier_value]

        if self.is_identifier(source):
            src_identifier = self.extract_identifier(source)
            src_index = index_value
        elif self.is_array_slice(source):
            src_id_token, src_slice = self.deconstruct_array_slice(source)
            src_identifier = self.extract_identifier(src_id_token)
            if any(
                comp is not None and not self.is_signed_integer(comp)
                for comp in src_slice
            ):
                raise JaqalError(f"Unresolved map element {identifier_value}")
            src_start, src_stop, src_step = [
                self.extract_signed_integer(comp) if comp is not None else comp
                for comp in src_slice
            ]
            limit = src_stop or maxsize
            src_start, src_stop, src_step = slice(
                src_start, src_stop, src_step
            ).indices(limit)
            src_range = range(src_start, src_stop, src_step)
            try:
                src_index = src_range[index_value]
            except IndexError:
                raise JaqalError(
                    f"Index {index_value} out of range for mapping {identifier_value}"
                )
        elif self.is_array_element(source):
            raise JaqalError(
                f"Cannot use map alias {identifier_value} as an array element"
            )
        else:
            raise JaqalError(f"Unknown map source format: {source}")

        return src_identifier, src_index

    def resolve_map_identifier(self, identifier_value):
        """Find the array element that maps to this identifier and return it."""

        if identifier_value not in self.map_dict:
            raise JaqalError(f"Cannot resolve map {identifier_value}")

        source = self.map_dict[identifier_value]

        if self.is_identifier(source):
            src_identifier = self.extract_identifier(source)
            if src_identifier in self.map_dict:
                res_identifier = self.resolve_map_identifier(src_identifier)
                return res_identifier
            else:
                raise JaqalError(
                    f"Cannot resolve map alias {identifier_value} to a register element"
                )
        elif self.is_array_slice(source):
            raise JaqalError(
                f"Cannot use map alias {identifier_value} as a gate argument"
            )
        elif self.is_array_element(source):
            src_id_token, src_index_token = self.deconstruct_array_element(source)
            src_identifier = self.extract_identifier(src_id_token)
            src_index = self.extract_signed_integer(src_index_token)
            res_identifier, res_index = self.resolve_map_element(
                src_identifier, src_index
            )
            return self.make_array_element_qual(
                self.make_qualified_identifier(res_identifier),
                self.make_signed_integer(res_index),
            )
        else:
            raise JaqalError(f"Unknown map source format: {source}")
