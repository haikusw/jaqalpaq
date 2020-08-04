# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Resolve references to macros to expansions of the gates they contain."""

from .tree import TreeRewriteVisitor
from .extract_macro import ExtractMacroVisitor
from jaqalpaq import JaqalError


def resolve_macro(tree, macro_dict):
    """Substitute the gates from the macro_dict into the tree, replacing all arguments as appropriate."""
    visitor = ResolveMacroVisitor(macro_dict)
    resolved_tree = visitor.visit(tree)
    return expand_redundant_blocks(resolved_tree)


class ResolveMacroVisitor(ExtractMacroVisitor):
    """Resolve macros both by expanding those defined in this tree and including any provided in the macro_dict
    argument. The user should *not* include macros defined in this tree in macro_dict, as it will then be impossible
    to tell when the macros were defined, which is an important part of Jaqal's syntactic restrictions.

    By deriving from ExtractMacroVisitor we get the definition for visit_macro_definition for free. It might be slightly
    more elegant if both classes got their definition of that method from a third source but this way works fine.
    """

    def __init__(self, macro_dict):
        super().__init__()
        self.macro_mapping.update(macro_dict)

    def visit_gate_statement(self, gate_name, gate_args):
        """If this gate statement is really a macro, replace it with the macro's block."""
        gate_name_key = self.extract_qualified_identifier(gate_name)
        if gate_name_key in self.macro_mapping:
            arguments, block = self.macro_mapping[gate_name_key]
            if len(arguments) != len(gate_args):
                raise JaqalError(
                    f"In resolving macro {gate_name_key}, expected {len(arguments)} arguments, found {len(gate_args)}"
                )
            arg_dict = {arg: gate_arg for arg, gate_arg in zip(arguments, gate_args)}
            return substitute_macro_arguments(block, arg_dict)
        return self.make_gate_statement(gate_name, gate_args)


def substitute_macro_arguments(tree, arg_dict):
    """Replace all occurrences of the given macro arguments with the values given in arg_dict."""
    visitor = MacroArgumentVisitor(arg_dict)
    return visitor.visit(tree)


class MacroArgumentVisitor(TreeRewriteVisitor):
    def __init__(self, arg_dict):
        self.arg_dict = arg_dict

    def visit_let_or_map_identifier(self, identifier):
        identifier_key = self.extract_qualified_identifier(identifier)
        if identifier_key in self.arg_dict:
            return self.arg_dict[identifier_key]
        return self.make_let_or_map_identifier(identifier)

    def visit_let_identifier(self, identifier):
        identifier_key = self.extract_qualified_identifier(identifier)
        if identifier_key in self.arg_dict:
            return self.arg_dict[identifier_key]
        return self.make_let_identifier(identifier)


def expand_redundant_blocks(tree):
    """In the course of expanding a macro, we may create sequential blocks nested inside other sequential blocks, and
    parallel blocks nested in other parallel blocks. This function undoes this."""

    visitor = RedundantBlockVisitor()
    return visitor.visit(tree)


class RedundantBlockVisitor(TreeRewriteVisitor):
    def visit_program(self, header_statements, body_statements):
        expanded_body_statements = []
        for stmt in body_statements:
            if self.is_sequential_gate_block(stmt):
                sub_statements = self.deconstruct_sequential_gate_block(stmt)
                expanded_body_statements.extend(sub_statements)
            else:
                expanded_body_statements.append(stmt)
        return self.make_program(header_statements, expanded_body_statements)

    def visit_sequential_gate_block(self, statements):
        expanded_statements = []
        for stmt in statements:
            if self.is_sequential_gate_block(stmt):
                sub_statements = self.deconstruct_sequential_gate_block(stmt)
                expanded_statements.extend(sub_statements)
            else:
                expanded_statements.append(stmt)
        return self.make_sequential_gate_block(expanded_statements)

    def visit_parallel_gate_block(self, statements):
        expanded_statements = []
        for stmt in statements:
            if self.is_parallel_gate_block(stmt):
                sub_statements = self.deconstruct_parallel_gate_block(stmt)
                expanded_statements.extend(sub_statements)
            else:
                expanded_statements.append(stmt)
        return self.make_parallel_gate_block(expanded_statements)
