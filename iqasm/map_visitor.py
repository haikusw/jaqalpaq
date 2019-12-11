from .parse import TreeRewriteVisitor


def expand_map_values(tree):
    """Remove all map statements and replace all references to mapped arrays with references to the underlying
    qubit registers."""

    transformer = MapTransformer()
    return transformer.visit(tree)


class MapTransformer(TreeRewriteVisitor):
    """A transformer that replaces mapped entries with register entries."""

    def __init__(self):
        # Mapping of register names to their size, used to validate map statements.
        self.registers = {}

        # Map aliases to (register-name, register-range) triplets
        self.mapping = {}

    def visit_register_statement(self, array_declaration):
        """Record information about the given register. We check that map statements are compatible with
        register statements."""
        identifier, size = self.deconstruct_array_declaration(array_declaration)
        if self.is_identifier(size):
            raise ValueError(f"Register has unresolved size {self.extract_identifier(size)}")
        assert self.is_integer(size)
        # Although in general this is not the right place to check for register inconsistencies, the errors might
        # be too confusing if we ignored the double register declaration error.
        identifier = self.extract_identifier(identifier)
        if identifier in self.registers:
            raise ValueError(f"Register {identifier} already declared")
        self.registers[identifier] = self.extract_integer(size)

        return self.make_register_statement(array_declaration)

    def visit_map_statement(self, target, source):
        """Create a mapping entry for this alias to the appropriate register."""
        dst_identifier = self.extract_identifier(target)

        if self.is_identifier(source):
            src_identifier = self.extract_identifier(source)
            src_range = None
        elif self.is_array_slice(source):
            src_id_token, src_slice_tokens = self.deconstruct_array_slice(source)
            src_identifier = self.extract_identifier(src_id_token)
            src_range = range(*[self.extract_token(token) for token in src_slice_tokens])
        elif self.is_array_element(source):
            src_id_token, src_element = self.deconstruct_array_element(source)
            src_identifier = self.extract_identifier(src_id_token)
            src_range = self.extract_integer(src_element)
        else:
            raise ValueError(f"Unknown map source format: {source}")

        if src_identifier not in self.registers:
            raise ValueError(f'Map statement references unknown register {src_identifier}')
        if dst_identifier in self.mapping:
            raise ValueError(f'Map statement references existing alias {dst_identifier}')

        self.mapping[dst_identifier] = (src_identifier, src_range)

        # Remove the map statement
        return None

    def visit_array_element(self, identifier, index):
        """Make sure an array element is either a register or an alias, and if it is an alias, remap it to its
        register."""

        if self.is_identifier(index):
            # We assume that all let-statement references have been resolved to specific numbers by now.
            raise ValueError(f"Cannot check unresolved array index {index}")

        extracted_id = self.extract_identifier(identifier)
        extracted_index = self.extract_integer(index)

        if extracted_id in self.mapping:
            mapped_identifier, mapped_index = self._map_array_element(extracted_id, extracted_index)
            identifier = self.make_identifier(mapped_identifier)
            index = self.make_integer(mapped_index)
        elif extracted_id not in self.registers:
            raise ValueError(f"Unknown array {extracted_id}")

        return self.make_array_element(identifier, index)

    def _map_array_element(self, identifier, index):
        """Map an alias array element to the appropriate register location.

        identifier -- A Python string representing the identifier's alias.

        index -- The Python integer index.

        Return a (register, index) tuple in Python types.

        """

        register_id, register_range = self.mapping[identifier]

        if register_range is None:
            return register_id, self.extract_integer(index)

        try:
            register_index = register_range[index]
        except IndexError:
            raise ValueError(f"Array element {identifier}[{index}] out of range")

        return register_id, register_index
