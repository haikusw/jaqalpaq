"""Parsing related functions and data types"""

from abc import ABC, abstractmethod
import pathlib

from lark import Lark, Transformer, Tree, Token


def parse_with_lark(text_or_fd, *args, **kwargs):
    """Parse the given text or file descriptor using Lark. Return the Lark parse tree."""
    parser = make_lark_parser(*args, **kwargs)
    tree = parser.parse(text_or_fd)
    return tree


def make_lark_parser(*args, **kwargs):
    """Create a lark parser with some default arguments."""
    kwargs_with_defaults = {
        'start': 'start',
        'parser': 'lalr',
        **kwargs
    }
    with open(get_grammar_path(), 'r') as fd:
        parser = Lark(fd, *args, **kwargs_with_defaults)
    return parser


def get_grammar_path(filename='iqasm_grammar.lark'):
    """Return the path to the lark grammar file."""
    return pathlib.Path(__file__).parent / filename


class VisitTransformer(Transformer):
    """A Lark transformer that traverses the tree and calls the appropriate methods in the ParseTreeVisitor class.

    If you're unsure of whether you should be using this class, you should not be using this class.
    """

    def __init__(self, visitor):
        super().__init__(visit_tokens=True)
        self._visitor = visitor

    def start(self, args):
        header_statements, body_statements = args
        return self._visitor.visit_program(header_statements, body_statements)

    def register_statement(self, args):
        array_declaration, = args
        return self._visitor.visit_register_statement(array_declaration)

    def map_statement(self, args):
        target, source = args
        return self._visitor.visit_map_statement(target, source)

    def let_statement(self, args):
        identifier, number = args
        return self._visitor.visit_let_statement(identifier, number)

    def body_statements(self, args):
        return [stmt for stmt in args if stmt is not None]

    def header_statements(self, args):
        return [stmt for stmt in args if stmt is not None]

    def gate_statement(self, args):
        gate_name = args[0]
        gate_args = args[1:]
        return self._visitor.visit_gate_statement(gate_name, gate_args)

    def macro_definition(self, args):
        identifiers = args[0].children
        gate_block = args[1]
        macro_name = identifiers[0]
        macro_args = identifiers[1:]
        return self._visitor.visit_macro_definition(macro_name, macro_args, gate_block)

    def macro_header(self, args):
        macro_name = args[0]
        macro_args = args[1:]
        ret = self._visitor.visit_macro_header(macro_name, macro_args)
        if ret is None:
            # This allows macro_header to be optional in the visitor
            return Tree('macro_header', args)
        else:
            return ret

    def loop_statement(self, args):
        repetition_count, block = args
        return self._visitor.visit_loop_statement(repetition_count, block)

    def sequential_gate_block(self, args):
        return self._visitor.visit_sequential_gate_block(args)

    def parallel_gate_block(self, args):
        return self._visitor.visit_parallel_gate_block(args)

    def array_declaration(self, args):
        identifier, size = args
        return self._visitor.visit_array_declaration(identifier, size)

    def array_element(self, args):
        identifier, index = args
        return self._visitor.visit_array_element(identifier, index)

    def array_slice(self, args):
        identifier = args[0]
        slice_args = args[1:]
        index_slice = slice(*slice_args)
        return self._visitor.visit_array_slice(identifier, index_slice)

    def let_identifier(self, args):
        identifier = args[0]
        return self._visitor.visit_let_identifier(identifier)

    def let_or_map_identifier(self, args):
        identifier = args[0]
        return self._visitor.visit_let_or_map_identifier(identifier)

    def IDENTIFIER(self, string):
        return self._visitor.visit_identifier(string)

    def SIGNED_NUMBER(self, string):
        return self._visitor.visit_signed_number(string)

    def NUMBER(self, string):
        return self._visitor.visit_number(string)

    def INTEGER(self, string):
        return self._visitor.visit_integer(string)

    def SIGNED_INTEGER(self, string):
        return self._visitor.visit_signed_integer(string)


class ParseTreeVisitor(ABC):
    """A visitor used to traverse a parse tree. Although it works directly on parse trees used by the underlying
    parser library, the user is not exposed to this detail.

    Methods in this visitor are designed to be overridden. Those without default implementations (mostly token-level
    methods) must be overridden to implement the visitor. The parse tree is visited from the bottom up. Therefore
    each method gets the results of lower visitations as its arguments, except for tokens, which get the raw string if
    they are overridden.

    """

    # Derived classes may overwrite this to change behavior.
    transformer_class = VisitTransformer

    def visit(self, tree):
        """Visit this tree and return the result of successively calling the visit_* methods."""
        transformer = VisitTransformer(self)
        return transformer.transform(tree)

    ##
    # Token-level methods
    #

    def visit_identifier(self, identifier_string):
        return str(identifier_string)

    def visit_signed_number(self, string):
        if '.' in string or 'e' in string or 'E' in string:
            return float(string)
        else:
            return int(string)

    def visit_number(self, string):
        if '.' in string or 'e' in string or 'E' in string:
            return float(string)
        else:
            return int(string)

    def visit_integer(self, string):
        return int(string)

    def visit_signed_integer(self, string):
        return int(string)

    ##
    # Mandatory overrides
    #

    @abstractmethod
    def visit_program(self, header_statements, body_statements):
        """Visit the 'start' rule in the grammar. Header statements and body statements are automatically gathered
        into a list after calling the appropriate header or body statement on each."""
        pass

    @abstractmethod
    def visit_register_statement(self, array_declaration):
        pass

    @abstractmethod
    def visit_map_statement(self, target, source):
        pass

    @abstractmethod
    def visit_let_statement(self, identifier, number):
        pass

    @abstractmethod
    def visit_gate_statement(self, gate_name, gate_args):
        """Visit a gate. The args are gathered into a list or identifiers, numbers, and array elements."""
        pass

    @abstractmethod
    def visit_macro_definition(self, name, arguments, block):
        """Visit a macro definition. The arguments are gathered into a list, but the block is merely the result of
        the appropriate visit_*_block method."""
        pass

    def visit_macro_header(self, name, arguments):
        """Visit the head of a macro. This override is optional as the information will be passed to
        visit_macro_definiton."""
        pass

    @abstractmethod
    def visit_loop_statement(self, repetition_count, block):
        """Visit a loop statement. The repetition count is either an integer or identifier."""
        pass

    @abstractmethod
    def visit_sequential_gate_block(self, statements):
        """Visit a gate block of sequential statements. Each statement is a gate statement, macro definition, or
        loop statement. Therefore it is important to be able to differentiate between the results of the appropriate
        visit_* methods."""
        pass

    @abstractmethod
    def visit_parallel_gate_block(self, statements):
        """Same as visit_sequential_gate_block, but intended for parallel execution."""
        pass

    @abstractmethod
    def visit_array_declaration(self, identifier, size):
        """Visit an array declaration, currently used in map and register statements. The identifier is the label
        the user wishes to use, and the size is either an identifier or integer."""
        pass

    @abstractmethod
    def visit_array_element(self, identifier, index):
        """Visit an array, dereferenced to a single element. The index is either an identifier or integer."""
        pass

    @abstractmethod
    def visit_array_slice(self, identifier, index_slice):
        """Visit an array dereferenced by slice, as used in the map statement. The identifier is the name of the
        existing array, and index_slice is a Python slice object. None represents the lack of a bound, an integer a
        definite bound, and a string is an identifier used as that bound."""
        pass

    @abstractmethod
    def visit_let_identifier(self, identifier):
        """Visit an identifier that can only exist if it was previously declared by a let statement."""
        pass

    @abstractmethod
    def visit_let_or_map_identifier(self, identifier):
        """Visit an identifier that must be declared in either a let or map statement."""
        pass


class TreeRewriteVisitor(ParseTreeVisitor):
    """A base class that serves to mostly rewrite a parse tree without knowing the exact implementation of the tree.
    Each method by default returns or reconstructs its portion of the tree."""

    ##
    # Overrides of visit methods
    #

    def visit_identifier(self, token):
        return token

    def visit_signed_number(self, token):
        return token

    def visit_number(self, token):
        return token

    def visit_integer(self, token):
        return token

    def visit_signed_integer(self, token):
        return token

    def visit_program(self, header_statements, body_statements):
        return self.make_program(header_statements, body_statements)

    def visit_register_statement(self, array_declaration):
        return self.make_register_statement(array_declaration)

    def visit_map_statement(self, target, source):
        return self.make_map_statement(target, source)

    def visit_let_statement(self, identifier, number):
        return self.make_let_statement(identifier, number)

    def visit_gate_statement(self, gate_name, gate_args):
        return self.make_gate_statement(gate_name, gate_args)

    def visit_macro_definition(self, name, arguments, block):
        return self.make_macro_definition(name, arguments, block)

    def visit_loop_statement(self, repetition_count, block):
        return self.make_loop_statement(repetition_count, block)

    def visit_sequential_gate_block(self, statements):
        return self.make_sequential_gate_block(statements)

    def visit_parallel_gate_block(self, statements):
        return self.make_parallel_gate_block(statements)

    def visit_array_declaration(self, identifier, size):
        return self.make_array_declaration(identifier, size)

    def visit_array_element(self, identifier, index):
        return self.make_array_element(identifier, index)

    def visit_array_slice(self, identifier, index_slice):
        return self.make_array_slice(identifier, index_slice)

    def visit_let_identifier(self, identifier):
        return self.make_let_identifier(identifier)

    def visit_let_or_map_identifier(self, identifier):
        return self.make_let_or_map_identifier(identifier)

    ##
    # New methods to construct parts of the tree
    #

    def make_program(self, header_statements, body_statements):
        return Tree('start', [Tree('header_statements', header_statements), Tree('body_statements', body_statements)])

    def make_register_statement(self, array_declaration):
        return Tree('register_statement', [array_declaration])

    def make_map_statement(self, target, source):
        return Tree('map_statement', [target, source])

    def make_let_statement(self, identifier, number):
        return Tree('let_statement', [identifier, number])

    def make_gate_statement(self, gate_name, gate_args):
        return Tree('gate_statement', [gate_name] + gate_args)

    def make_macro_definition(self, name, arguments, block):
        macro_header = self.make_macro_header(name, arguments)
        return Tree('macro_definition', [macro_header, block])

    def make_macro_header(self, name, arguments):
        return Tree('macro_header', [name] + arguments)

    def make_loop_statement(self, repetition_count, block):
        return Tree('loop_statement', [self.enforce_integer_if_numeric(repetition_count), block])

    def make_sequential_gate_block(self, statements):
        return Tree('sequential_gate_block', statements)

    def make_parallel_gate_block(self, statements):
        return Tree('parallel_gate_block', statements)

    def make_array_declaration(self, identifier, size):
        return Tree('array_declaration', [identifier, self.enforce_integer_if_numeric(size)])

    def make_array_element(self, identifier, index):
        return Tree('array_element', [identifier, self.enforce_integer_if_numeric(index)])

    def make_array_slice(self, identifier, index_slice):
        # TODO: This is not quite right, but we should revisit this when correcting array slice semantics.
        index_start = self.enforce_integer_if_numeric(index_slice.start) if index_slice.start is not None else None
        index_stop = self.enforce_signed_integer_if_numeric(index_slice.stop) if index_slice.stop is not None else None
        index_step = self.enforce_signed_integer_if_numeric(index_slice.step) if index_slice.step is not None else None

        indices = [index for index in [index_start, index_stop, index_step] if index is not None]

        return Tree('array_slice', [identifier] + indices)

    def make_let_identifier(self, identifier):
        return Tree('let_identifier', [identifier])

    def make_let_or_map_identifier(self, identifier):
        return Tree('let_or_map_identifier', [identifier])

    def make_identifier(self, identifier_string):
        return Token('IDENTIFIER', identifier_string)

    def make_signed_number(self, number):
        if not isinstance(number, float) and not isinstance(number, int):
            raise TypeError(f"Expected number, found {number}")
        return Token('SIGNED_NUMBER', str(number))

    def make_number(self, number):
        if (not isinstance(number, float) and not isinstance(number, int)) or number < 0:
            raise TypeError(f"Expected non-negative number, found {number}")
        return Token('NUMBER', str(number))

    def make_integer(self, number):
        if not isinstance(number, int) or number < 0:
            raise TypeError(f"Expected non-negative integer, found {number}")
        return Token('INTEGER', str(number))

    def make_signed_integer(self, number):
        if not isinstance(number, int):
            raise TypeError(f"Expected integer, found {number}")
        return Token('SIGNED_INTEGER', str(number))

    def enforce_integer_if_numeric(self, number):
        if self.is_integer(number):
            return number
        elif self.is_signed_integer(number) or self.is_number(number) or self.is_signed_number(number):
            if float(number) < 0 or float(number) != int(number):
                raise ValueError(f'Expected integer, found {number}')
            return self.make_integer(int(number))
        else:
            # Likely an identifier
            return number

    def enforce_signed_integer_if_numeric(self, number):
        if self.is_signed_integer(number):
            return number
        elif self.is_integer(number):
            return self.make_signed_integer(int(number))
        elif self.is_number(number) or self.is_signed_number(number):
            if float(number) != int(number):
                raise ValueError(f"Expected signed integer, found {number}")
            return self.make_signed_integer(int(number))
        else:
            return number

    ##
    # New methods to check if a portion of a tree or token is of a given type
    #

    def is_program(self, tree):
        return self._is_tree(tree, 'start')

    def is_register_statement(self, tree):
        return self._is_tree(tree, 'register_statement')

    def is_map_statement(self, tree):
        return self._is_tree(tree, 'map_statement')

    def is_let_statement(self, tree):
        return self._is_tree(tree, 'let_statement')

    def is_body_statements(self, tree):
        # Note: The visitor would not visit this directly but as part of visiting the whole program
        return self._is_tree(tree, 'body_statements')

    def is_header_statements(self, tree):
        return self._is_tree(tree, 'header_statements')

    def is_gate_statement(self, tree):
        return self._is_tree(tree, 'gate_statement')

    def is_macro_definition(self, tree):
        return self._is_tree(tree, 'macro_definition')

    def is_loop_statement(self, tree):
        return self._is_tree(tree, 'loop_statement')

    def is_sequential_gate_block(self, tree):
        return self._is_tree(tree, 'sequential_gate_block')

    def is_parallel_gate_block(self, tree):
        return self._is_tree(tree, 'gate_block')

    def is_array_declaration(self, tree):
        return self._is_tree(tree, 'array_declaration')

    def is_array_element(self, tree):
        return self._is_tree(tree, 'array_element')

    def is_array_slice(self, tree):
        return self._is_tree(tree, 'array_slice')

    def is_identifier(self, token):
        return self._is_token(token, 'IDENTIFIER')

    def is_signed_number(self, token):
        return self._is_token(token, 'SIGNED_NUMBER')

    def is_number(self, token):
        return self._is_token(token, 'NUMBER')

    def is_integer(self, token):
        return self._is_token(token, 'INTEGER')

    def is_signed_integer(self, token):
        return self._is_token(token, 'SIGNED_INTEGER')

    @staticmethod
    def _is_tree(tree, data):
        return isinstance(tree, Tree) and tree.data == data

    @staticmethod
    def _is_token(token, data):
        return isinstance(token, Token) and token.type == data

    ##
    # Deconstruct trees and tokens into their parts, used to go top down instead of (actually in addition to) bottom-up
    #

    def deconstruct_array_declaration(self, tree):
        """Return the portion of the tree that is the identifier and the size."""
        identifier, size = tree.children
        return identifier, size

    def deconstruct_array_slice(self, tree):
        """Return the portion of the tree that is the identifier and a 3-tuple with tokens representing the slice."""
        identifier = tree.children[0]
        slice_args = tree.children[1:]
        if len(slice_args) == 1:
            slice_args = (None, slice_args[0], None)
        elif len(slice_args) == 2:
            slice_args = (slice_args[0], slice_args[1], None)
        elif len(slice_args) == 3:
            slice_args = tuple(slice_args)
        else:
            raise ValueError(f"Expected 1, 2, or 3 element slice, found {slice_args}")

        return identifier, slice_args

    def deconstruct_array_element(self, tree):
        """Return the portion of the tree that is the identifier and the index."""
        identifier, index = tree.children
        return identifier, index

    def extract_identifier(self, token):
        """Return an identifier as a string."""
        return str(token)

    def extract_integer(self, token):
        return int(token)

    def extract_signed_integer(self, token):
        return int(token)

    def extract_number(self, token):
        return float(token)

    def extract_signed_number(self, token):
        return float(token)

    def extract_token(self, token):
        """Figure out what the token is and call the appropriate extract method."""
        if self.is_identifier(token):
            return self.extract_identifier(token)
        elif self.is_integer(token):
            return self.extract_integer(token)
        elif self.is_signed_integer(token):
            return self.extract_signed_integer(token)
        elif self.is_number(token):
            return self.extract_number(token)
        elif self.is_signed_number(token):
            return self.extract_signed_number(token)
        else:
            raise TypeError(f"Unknown token: {token}")

    def extract_array_slice(self, tree):
        """Return a Python slice object from the given tree."""
        # TODO: Fix this when we fix array slice semantics
        def extract_value(arg):
            if self.is_identifier(arg):
                return self.extract_identifier(arg)
            elif self.is_integer(arg):
                return self.extract_integer(arg)
            elif self.is_signed_integer(arg):
                return self.extract_signed_integer(arg)
            else:
                raise ValueError(f"Unknown tree in array slice: {arg}")
        args = [extract_value(arg) for arg in tree.children[1:]]
        if len(args) > 3:
            raise ValueError(f"Too many slice arguments")
        return slice(*args)