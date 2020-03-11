"""Provide an interface to the parsing functions that also caches computation and allows for re-evaluation with
different constant values."""

from .parse import parse_with_lark, TreeRewriteVisitor
from .extract_let import extract_let
from .extract_map import extract_map
from .resolve_let import resolve_let, combine_let_dicts
from .resolve_map import resolve_map
from .resolve_macro import resolve_macro
from .block_normalizer import normalize_blocks_with_unitary_timing
from .iter_gates import get_gates_and_loops
from .validate import validate


class Interface:

    @classmethod
    def from_file(cls, root_filename):
        """Create a new interface from a file."""
        with open(root_filename, 'r') as fd:
            return cls(fd.read())

    def __init__(self, root_text):
        """Create a new interface using root_text as the text of the main Jaqal file."""

        self._registers = None

        self._let_dict = None
        self._map_dict = None

        self._initial_tree = None

        self._init_parse_tree(root_text)

    @property
    def exported_constants(self):
        """Return a dictionary mapping tuples of qualified identifiers to the numeric values they have by default
        in the file."""
        return self._let_dict

    def get_uniformly_timed_gates_and_registers(self, override_dict):
        """Parse the input down to a sequence of gates with arguments that are either qubit register elements or
        numbers.

        override_dict -- Use these values instead of the values defined in the exported let statements. All keys in
        this dict must be present as let statements. Any values not overridden by this dict retain their original
        value.

        Note: there is no way currently to override register mappings or macros.

        Return a list of Gate and aggregate objects and a dictionary mapping register names to their size.

        """

        full_let_dict = combine_let_dicts(self._let_dict, override_dict)
        tree = resolve_let(self._initial_tree, full_let_dict)
        map_dict = {key: resolve_let(value, full_let_dict) for key, value in self._map_dict.items()}
        tree = resolve_map(tree, map_dict, self._registers)
        tree = normalize_blocks_with_unitary_timing(tree)
        registers = {str(name): convert_to_int(resolve_let(value, full_let_dict))
                     for name, value in self._registers.items()}
        validate(tree, registers)
        return get_gates_and_loops(tree), registers

    ##
    # Private methods
    #

    def _init_parse_tree(self, text):
        tree = parse_with_lark(text)

        # We extract let constants in one way to present them to the user of this interface, and another way to
        # use in transforming the various parse trees.
        self._let_dict = extract_let(tree, use_float=True)

        self._map_dict, self._registers = extract_map(tree)

        tree = resolve_macro(tree, {})  # The extra argument may be used for imported macros
        self._initial_tree = strip_headers_and_macro_definitions(tree)

def convert_to_int(token):
    float_value = float(token)
    int_value = int(float_value)
    if int_value != float_value:
        raise ValueError(f"Invalid register size {float_value}")
    return int_value


def strip_headers_and_macro_definitions(tree):
    """Return a tree without any header statements or macro definitions."""
    visitor = StripHeadersAndMacroDefinitionsVisitor()
    return visitor.visit(tree)


class StripHeadersAndMacroDefinitionsVisitor(TreeRewriteVisitor):

    def visit_register_statement(self, array_declaration):
        return None

    def visit_map_statement(self, target, source):
        return None

    def visit_let_statement(self, identifier, number):
        return None

    def visit_macro_definition(self, name, arguments, block):
        return None
