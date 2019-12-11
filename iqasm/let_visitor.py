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


class LetTransformer(MacroContextRewriteVisitor):
    """A Transformer that automatically fills in let values. We use a lark transformer so that we can chain
    this """

    def __init__(self, override_dict):
        super().__init__()
        self.mapping = {}
        self.override_dict = {label: self.make_signed_number(value) for label, value in override_dict.items()}

    def visit_let_statement(self, identifier, number):
        if identifier in self.mapping:
            raise ValueError(f'Redefinition of let value {identifier}')
        self.mapping[identifier] = self.override_dict.get(identifier, number)
        # Return value of None effectively removes this statement from the parse tree
        return None

    def visit_let_identifier(self, identifier):
        if identifier in self.mapping:
            return self.mapping[identifier]
        else:
            raise ValueError(f"Unknown identifier {identifier}")

    def visit_let_or_map_identifier(self, identifier):
        if identifier in self.mapping and not self._is_identifier_shadowed(identifier):
            return self.mapping[identifier]
        else:
            # This could be an alias with the map statement.
            return self.make_let_or_map_identifier(identifier)

    def _is_identifier_shadowed(self, identifier):
        """Return if this identifier is currently shadowed by a local macro argument."""
        return self.macro_args is not None and identifier in self.macro_args
