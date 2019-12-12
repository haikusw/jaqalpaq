import itertools

from .parse import TreeRewriteVisitor
from .macro_context_visitor import MacroContextRewriteVisitor


def expand_macros(tree):
    """Replace all macro invocations with their expanded gates, gate blocks, and loops."""

    transformer = ExpandMacroTransformer()
    return transformer.visit(tree)


class ExpandMacroTransformer(MacroContextRewriteVisitor):
    """A visitor that transforms a parse tree into another with all macros fully expanded."""

    def __init__(self):
        super().__init__()
        self.macro_definitions = {}

    def visit_program(self, header_statements, body_statements):
        unraveled_statements = []
        for stmt in body_statements:
            if isinstance(stmt, list):
                unraveled_statements.extend(stmt)
            else:
                unraveled_statements.append(stmt)
        return self.make_program(
            header_statements,
            unraveled_statements
        )

    def visit_gate_statement(self, gate_name, gate_args):
        if gate_name in self.macro_definitions:
            return self._substitute_macro(gate_name, gate_args)
        else:
            return self.make_gate_statement(gate_name, gate_args)

    def visit_macro_definition(self, name, arguments, block):
        # Block is actually a list of the statements in the block thanks to visit_macro_gate_block
        self.macro_definitions[name] = (arguments, block)

    def visit_macro_gate_block(self, block):
        if self.is_sequential_gate_block(block):
            statements = self.deconstruct_sequential_gate_block(block)
        elif self.is_parallel_gate_block(block):
            statements = self.deconstruct_parallel_gate_block(block)
        else:
            raise ValueError(f"Unknown gate block {block}")
        return statements

    def _substitute_macro(self, macro_name, gate_args):
        """Return a list of statements from the given macro with its parameters replaced by gate_args."""
        macro_args, statements = self.macro_definitions[macro_name]
        if len(macro_args) != len(gate_args):
            raise ValueError(f"Macro argument count mismatch in invocation of {macro_name}")
        argdict = {
            macro_arg: gate_arg for gate_arg, macro_arg in zip(gate_args, macro_args)
        }
        visitor = MacroSubstituteVisitor(argdict)
        sub_statements = [visitor.visit(stmt) for stmt in statements]
        return sub_statements


class MacroSubstituteVisitor(TreeRewriteVisitor):
    """A visitor that is used to substitute arguments to gates with those given in a dictionary to the constructor."""

    def __init__(self, subdict):
        super().__init__()
        self.subdict = subdict

    def visit_let_or_map_identifier(self, identifier):
        if identifier in self.subdict:
            return self.subdict[identifier]
        else:
            return self.make_let_or_map_identifier(identifier)

    def visit_let_identifier(self, identifier):
        if identifier in self.subdict:
            return self.subdict[identifier]
        else:
            return self.make_let_identifier(identifier)
