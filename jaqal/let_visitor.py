from .macro_context_visitor import MacroContextRewriteVisitor


def expand_let_values(tree, override_dict=None):
    """Remove all let-statements from the parse tree and fill in instances of let-values with the concrete value
    they represent.

    tree - The tree produced by parsing with Lark.

    override_dict -- A dictionary of values to use instead of the values presented in the let-statements.

    Return a tree suitable for sending to other ParseTreeVisitors.

    """

    override_dict = override_dict or {}
    transformer = LetTransformer(override_dict)
    return transformer.visit(tree)


def export_let_symbols(tree):
    """Return a dictionary mapping let symbols found in this tree to their value."""
    transformer = LetTransformer({})
    transformer.visit(tree)
    return transformer.mapping


class LetTransformer(MacroContextRewriteVisitor):
    """A Transformer that automatically fills in let values. We use a lark transformer so that we can chain
    this """

    def __init__(self, override_dict):
        super().__init__()
        self.mapping = {}
        self.override_dict = {(label,): self.make_signed_number(value) for label, value in override_dict.items()}

    def visit_let_statement(self, identifier, number):
        identifier_tuple = (str(identifier),)
        if identifier_tuple in self.mapping:
            raise ValueError(f'Redefinition of let value {identifier_tuple}')
        self.mapping[identifier_tuple] = self.override_dict.get(identifier_tuple, number)
        # Return value of None effectively removes this statement from the parse tree
        return None

    def visit_let_identifier(self, identifier):
        identifier_tuple = self.extract_qualified_identifier(identifier)
        if identifier_tuple in self.mapping and not self._is_identifier_shadowed(identifier_tuple):
            return self.mapping[identifier_tuple]
        else:
            # This would still be valid if i.e. we are inside a macro definition.
            return self.make_let_identifier(identifier)

    def visit_let_or_map_identifier(self, identifier):
        identifier_tuple = self.extract_qualified_identifier(identifier)
        if identifier_tuple in self.mapping and not self._is_identifier_shadowed(identifier_tuple):
            return self.mapping[identifier_tuple]
        else:
            # This could be an alias with the map statement.
            return self.make_let_or_map_identifier(identifier)

    def _is_identifier_shadowed(self, identifier):
        """Return if this identifier is currently shadowed by a local macro argument."""
        return self.macro_args is not None and identifier in self.macro_args
