from .parse import TreeRewriteVisitor
from .macro_context_visitor import MacroContextRewriteVisitor
from .identifier import Identifier

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
        ret_body_statements = []

        for stmt in body_statements:
            if isinstance(stmt, SequentialBlock):
                ret_body_statements.extend(stmt.statements)
            elif isinstance(stmt, ParallelBlock):
                ret_body_statements.append(self.make_parallel_gate_block(stmt.statements))
            else:
                ret_body_statements.append(stmt)

        return self.make_program(header_statements, ret_body_statements)

    def visit_parallel_gate_block(self, statements):
        ret_statements = []
        for stmt in statements:
            if isinstance(stmt, ParallelBlock):
                ret_statements.extend(stmt.statements)
            elif isinstance(stmt, SequentialBlock):
                ret_statements.append(self.make_sequential_gate_block(stmt.statements))
            else:
                ret_statements.append(stmt)
        return self.make_parallel_gate_block(ret_statements)

    def visit_sequential_gate_block(self, statements):
        ret_statements = []
        for stmt in statements:
            if isinstance(stmt, SequentialBlock):
                ret_statements.extend(stmt.statements)
            elif isinstance(stmt, ParallelBlock):
                ret_statements.append(self.make_parallel_gate_block(stmt.statements))
            else:
                ret_statements.append(stmt)
        return self.make_sequential_gate_block(ret_statements)

    def visit_gate_statement(self, gate_name, gate_args):
        qual_gate_name = self.extract_qualified_identifier(gate_name)

        if qual_gate_name in self.macro_definitions:
            return self._substitute_macro(qual_gate_name, gate_args)
        else:
            return self.make_gate_statement(gate_name, gate_args)

    def visit_macro_definition(self, name, arguments, block):
        if self.is_sequential_gate_block(block):
            statements = self.deconstruct_sequential_gate_block(block)
            is_sequential = True
        elif self.is_parallel_gate_block(block):
            statements = self.deconstruct_parallel_gate_block(block)
            is_sequential = False
        else:
            raise ValueError(f"Unknown gate block {block}")

        name = Identifier.parse(name)
        arguments = [Identifier.parse(arg) for arg in arguments]

        self.macro_definitions[name] = (arguments, statements, is_sequential)

    def visit_macro_gate_block(self, block):
        return block

    def _substitute_macro(self, macro_name, gate_args):
        """Return a block of statements from the given macro with its parameters replaced by gate_args."""
        macro_args, statements, is_sequential = self.macro_definitions[macro_name]
        if len(macro_args) != len(gate_args):
            raise ValueError(f"Macro argument count mismatch in invocation of {macro_name}")
        argdict = {
            macro_arg: gate_arg for gate_arg, macro_arg in zip(gate_args, macro_args)
        }
        visitor = MacroSubstituteVisitor(argdict)
        sub_statements = [visitor.visit(stmt) for stmt in statements]
        if is_sequential:
            return SequentialBlock(sub_statements)
        else:
            return ParallelBlock(sub_statements)


class MacroSubstituteVisitor(TreeRewriteVisitor):
    """A visitor that is used to substitute arguments to gates with those given in a dictionary to the constructor."""

    def __init__(self, subdict):
        super().__init__()
        self.subdict = subdict

    def visit_let_or_map_identifier(self, identifier):
        if self.is_qualified_identifier(identifier):
            identifier_key = self.extract_qualified_identifier(identifier)
            if identifier_key in self.subdict:
                return self.subdict[identifier_key]
        return self.make_let_or_map_identifier(identifier)

    def visit_let_identifier(self, identifier):
        if identifier in self.subdict:
            return self.subdict[identifier]
        else:
            return self.make_let_identifier(identifier)


# We use these special classes to distinguish between blocks introduced by substitution and blocks that the user
# specifically added.

class SequentialBlock:
    def __init__(self, statements):
        self.statements = statements


class ParallelBlock:
    def __init__(self, statements):
        self.statements = statements
