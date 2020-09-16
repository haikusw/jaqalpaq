# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
"""Provide an interface to the parsing functions that also caches computation and allows for re-evaluation with
different constant values."""

from functools import lru_cache

from .tree import parse_with_lark, TreeRewriteVisitor
from .extract_let import extract_let
from .extract_map import extract_map
from .extract_usepulses import extract_usepulses
from .resolve_let import resolve_let, combine_let_dicts
from .resolve_map import resolve_map
from .resolve_macro import resolve_macro
from .block_normalizer import normalize_blocks_with_unitary_timing
from .iter_gates import get_gates_and_loops
from .validate import validate
from jaqalpaq import JaqalError


class Interface:
    @classmethod
    def from_file(cls, root_filename):
        """Create a new interface from a file."""
        with open(root_filename, "r") as fd:
            return cls(fd.read())

    def __init__(self, root_text, allow_no_usepulses=False):
        """Create a new interface using root_text as the text of the main Jaqal file.

        If unless allow_no_usepulses is True (default=False), then the use must provide a usepulses statement.
        """

        self._registers = None

        self._let_dict = None
        self._default_let_dict = None
        self._map_dict = None
        self._usepulses = None

        self._allow_no_usepulses = bool(allow_no_usepulses)

        self._initial_tree = None
        self._preprocessed_tree = None

        self._init_parse_tree(root_text)

    @property
    def tree(self):
        """Return the parse tree created when parsing the text given to the constructor. All functions that take a
        tree must either take this value (which happens if you don't give a tree) or a tree that is created from
        transforming this tree."""
        return self._initial_tree

    @property
    def preprocessed_tree(self):
        """Return the parse tree created when parsing the text after expanding macros and removing
        header statements. This tree has as much processing applied as can be done without knowing
        the let override dict."""
        assert (
            self._initial_tree is not None
        ), "Do not call before setting up the initial tree"
        if self._preprocessed_tree is None:
            tree = self.resolve_macro(self._initial_tree)
            self._preprocessed_tree = self.strip_metadata(tree)
        return self._preprocessed_tree

    @property
    def exported_constants(self):
        """Return a dictionary mapping tuples of qualified identifiers to the numeric values they have by default
        in the file."""
        return self._let_dict

    @property
    def usepulses(self):
        """Return a dictionary mapping qualified identifiers to the objects they import.
        See extract_usepulses for more details."""
        return self._usepulses

    def get_uniformly_timed_gates_and_registers(self, override_dict=None):
        """Parse the input down to a sequence of gates with arguments that are either qubit register elements or
        numbers.

        override_dict -- Use these values instead of the values defined in the exported let statements. All keys in
        this dict must be present as let statements. Any values not overridden by this dict retain their original
        value.

        Note: there is no way currently to override register mappings or macros.

        Return a list of Gate and aggregate objects and a dictionary mapping register names to their size.

        """

        let_dict = self.make_let_dict(override_dict)
        tree = self.resolve_let(self.preprocessed_tree, let_dict=let_dict)
        tree = self.resolve_map(tree, let_dict=let_dict)
        tree = normalize_blocks_with_unitary_timing(tree)
        registers = self.make_register_dict(let_dict)
        validate(tree, registers)
        return get_gates_and_loops(tree), registers

    def make_let_dict(self, override_dict=None):
        """Create a dictionary of all let values in the parse tree. The let values will map to parse trees. The result
        of this call is therefore mostly useful as an input to other methods of this class."""
        if override_dict is None:
            if self._default_let_dict is None:
                self._default_let_dict = combine_let_dicts(self._let_dict, {})
            return self._default_let_dict
        else:
            full_let_dict = combine_let_dicts(self._let_dict, override_dict)
            return full_let_dict

    @staticmethod
    def resolve_macro(tree, macro_dict=None):
        """Return a parse tree with all macros expanded. The macro definitions will still be present.

        tree -- A parse tree.

        macro_dict -- A dictionary with any additional macros not defined in the tree.
        """
        # Note: This should be a member variable set in the constructor once we allow importing macros.
        macro_dict = macro_dict or {}
        tree = resolve_macro(tree, macro_dict)
        return tree

    @staticmethod
    def strip_metadata(tree):
        """Remove all macro definitions and header statements from this tree."""
        return strip_headers_and_macro_definitions(tree)

    def resolve_let(self, tree, let_dict=None):
        """Resolve all the let statements in the tree and return the new tree.

        tree -- A parse tree derived from self.tree. This tree is not modified.

        let_dict -- A dictionary mapping identifiers to parse trees. Use make_let_dict() to create this.
        """

        let_dict = let_dict or self.make_let_dict()
        return resolve_let(tree, let_dict)

    def resolve_map(self, tree, let_dict=None):
        """Resolve all references to mapped registers with the actual register reference. This cannot properly handle
        unresolved let constants in the map definitions, therefore it is best to run after resolve_let.

        tree -- A parse tree derived from self.tree. This tree is not modified. If any map statements in this
        tree use let constants still, an error will result.

        let_dict -- A dictionary mapping identifiers to parse trees. Use make_let_dict() to create this.
        """
        let_dict = let_dict or self.make_let_dict()
        map_dict = {
            key: resolve_let(value, let_dict) for key, value in self._map_dict.items()
        }
        return resolve_map(tree, map_dict, self._registers)

    def make_register_dict(self, let_dict=None):
        """Create a dictionary mapping register identifiers to the number of qubits they hold as an integer.

        let_dict -- A dictionary mapping identifiers to parse trees. Use make_let_dict() to create this.
        """
        let_dict = let_dict or self.make_let_dict()
        registers = {
            str(name): convert_to_int(resolve_let(value, let_dict))
            for name, value in self._registers.items()
        }
        return registers

    ##
    # Private methods
    #

    def _init_parse_tree(self, text):
        tree = parse_with_lark(text)
        self._initial_tree = tree

        # We extract let constants in one way to present them to the user of this interface, and another way to
        # use in transforming the various parse trees.
        self._let_dict = extract_let(tree, use_float=True)

        self._map_dict, self._registers = extract_map(tree)

        self._usepulses = extract_usepulses(tree)
        if (
            len(self._usepulses) > 1
            or not self._usepulses
            and not self._allow_no_usepulses
        ):
            raise JaqalError("At most one usepulses allowed for now")


class HashDict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


def make_hashable(value):
    if isinstance(value, dict):
        return HashDict(value)
    else:
        return value


memo_maxsize = 32


def memoize_method(func):
    memo_func = lru_cache(maxsize=memo_maxsize)(func)

    def inner(self, *args, **kwargs):
        args = tuple(make_hashable(arg) for arg in args)
        kwargs = {key: make_hashable(value) for key, value in sorted(kwargs.items())}
        return memo_func(self, *args, **kwargs)

    return inner


class MemoizedInterface(Interface):
    """An interface that is identical but memoizes certain calls."""

    @memoize_method
    def get_uniformly_timed_gates_and_registers(self, override_dict=None):
        return super().get_uniformly_timed_gates_and_registers(
            override_dict=override_dict
        )


def convert_to_int(token):
    float_value = float(token)
    int_value = int(float_value)
    if int_value != float_value:
        raise JaqalError(f"Invalid register size {float_value}")
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
