from .parse import TreeRewriteVisitor


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


class LetTransformer(TreeRewriteVisitor):
    """A Transformer that automatically fills in let values. We use a lark transformer so that we can chain
    this """

    def __init__(self, override_dict):
        self.mapping = {}
        self.override_dict = {label: self.make_signed_number(value) for label, value in override_dict.items()}

    def visit_let_statement(self, identifier, number):
        if identifier in self.mapping:
            raise ValueError(f'Redefinition of let value {identifier}')
        self.mapping[identifier] = self.override_dict.get(identifier, number)
        return self.make_let_statement(identifier, number)

    def visit_let_identifier(self, identifier):
        if identifier in self.mapping:
            return self.mapping[identifier]
        else:
            raise ValueError(f"Unknown identifier {identifier}")