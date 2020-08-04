# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Substitute let constant values into parse trees."""
from numbers import Integral

from .macro_context_visitor import MacroContextRewriteVisitor
from .tree import TreeManipulators
from jaqalpaq import JaqalError


def resolve_let(tree, let_dict):
    """Replace all let values in this tree with their values from the let dictionary. This may fail if resolution
    would result in a value that cannot occur in context, i.e. a floating point value where an integer is required."""

    if TreeManipulators.is_tree(tree):
        visitor = ResolveLetVisitor(let_dict)
        resolved = visitor.visit(tree)
        return resolved
    else:
        # Visitor objects can only handle trees, not tokens, and there are cases where it's convenient to do let-
        # resolution on an object that may be a token.
        if TreeManipulators.is_identifier(tree):
            identifier = TreeManipulators.extract_identifier(tree)
            if identifier in let_dict:
                return let_dict[identifier]
        return tree


def combine_let_dicts(let_dict, *additional_dicts):
    """Combine dictionaries. The first argument must be the default let values from the Jaqal file. It maps Identifiers
    to signed floats. The additional dictionaries are assumed to come from an external source and are can be either
    Identifiers or plain strings (with possible '.' characters) mapping to signed floats. The dictionaries are used
    one after another, stopping at first match. In other words, the first additional dict is of highest priority."""

    # Normalize the additional dictionaries.
    additional_dicts = [
        {str(key): float(value) for key, value in ad.items()} for ad in additional_dicts
    ]
    let_str_dict = {str(key): value for key, value in let_dict.items()}

    # Make sure every value in each additional dict occurred in the let dict
    for ad in additional_dicts:
        for key in ad:
            if key not in let_str_dict:
                raise JaqalError(f"Attempted to override unknown let {key}")

    def get_value(key):
        key = str(key)
        for ad in additional_dicts:
            if key in ad:
                return ad[key]
        return let_str_dict[key]

    combined_dict = {key: get_value(key) for key in let_dict}
    return combined_dict


class ResolveLetVisitor(MacroContextRewriteVisitor):
    def __init__(self, let_dict):
        super().__init__()
        self.let_dict = let_dict

    def lookup_let(self, key):
        return self.let_dict.get(key)

    def has_let(self, key):
        return key in self.let_dict

    def visit_let_identifier(self, identifier):
        identifier_value = self.extract_qualified_identifier(identifier)
        if self.has_let(identifier_value) and not self.is_macro_argument(
            identifier_value
        ):
            return self.make_signed_number(self.lookup_let(identifier_value))
        else:
            return self.make_let_identifier(identifier)

    def visit_let_or_map_identifier(self, identifier):
        identifier_value = self.extract_qualified_identifier(identifier)
        if self.has_let(identifier_value) and not self.is_macro_argument(
            identifier_value
        ):
            return self.make_signed_number(self.lookup_let(identifier_value))
        else:
            return self.make_let_or_map_identifier(identifier)

    def visit_loop_statement(self, repetition_count, block):
        """Validate the repetition count is a non-negative integer."""
        num = self.extract_signed_number(repetition_count)
        if not is_non_negative_integer(num):
            raise JaqalError(
                f"While resolving let values: illegal loop statement count: {num}"
            )
        return self.make_loop_statement(repetition_count, block)

    def visit_array_declaration(self, identifier, size):
        """Validate the size is a non-negative integer."""
        num = self.extract_signed_number(size)
        if not is_non_negative_integer(num):
            raise JaqalError(
                f"While resolving let values: illegal array declaration size: {num}"
            )
        return self.make_array_declaration(identifier, size)

    def visit_array_element(self, identifier, index):
        """Validate the index is an integer."""
        num = self.extract_signed_number(index)
        if not is_integer(num):
            raise JaqalError(f"While resolving let values: illegal array index {num}")
        return self.make_array_element(identifier, index)

    def visit_array_element_qual(self, identifier, index):
        """Validate the index is an integer."""
        num = self.extract_signed_number(index)
        if not is_integer(num):
            raise JaqalError(f"While resolving let values: illegal array index {num}")
        return self.make_array_element_qual(identifier, index)

    def visit_array_slice(self, identifier, index_slice):
        """Validate all parts of the slice are integers."""
        for value in [index_slice.start, index_slice.stop, index_slice.step]:
            if value is not None:
                num = self.extract_signed_number(value)
                if not is_integer(num):
                    raise JaqalError(
                        f"While resolving let values: illegal array slice value {num}"
                    )
        return self.make_array_slice(identifier, index_slice)

    def is_macro_argument(self, identifier):
        """Return whether we are in a macro definition and if so if this identifier is the same as one of the
        macro arguments."""
        return self.in_macro and identifier in self.macro_args


def is_non_negative_integer(num):
    return is_integer(num) and num >= 0


def is_integer(num):
    return isinstance(num, Integral) or int(num) == num
