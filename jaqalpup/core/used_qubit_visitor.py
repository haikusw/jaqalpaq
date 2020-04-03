from collections import defaultdict

from jaqalpup.core.visitor import Visitor


def get_used_qubit_indices(obj, context=None, macros=None):
    """Recursively find all qubits used in this object.
    :param obj: The instruction to query; defaults to the entire circuit.
    :type obj: BlockStatement or None
    :param context: If using this method to inspect an instruction in a macro call, provides information about the current scope. Unless you know precisely what you're doing, you should most likely omit this.
    :type context: dict
    :param Optional[dict] macros: Use these macros.
    :returns: A dict mapping fundamental register names to sets of the indices within those registers which are used by the instruction.
    """

    visitor = UsedQubitIndicesVisitor()
    # Note: If we add a reference to its definition to each gate we don't need
    # the macros argument.
    return visitor.visit(obj, context=context, macros=macros)


class UsedQubitIndicesVisitor(Visitor):

    def visit_default(self, obj, *args, **kwargs):
        """Anything that isn't explicitly listed here can't have any qubits."""
        return {}

    def visit_LoopStatement(self, obj, context=None, macros=None):
        return self.visit(obj, context=context, macros=macros)

    def visit_BlockStatement(self, obj, context=None, macros=None):
        indices = defaultdict(set)
        for sub_obj in obj:
            self.merge_into(indices, self.visit(sub_obj, context=context, macros=macros))
        return indices

    def visit_ScheduledCircuit(self, obj, context=None, macros=None):
        if macros is None:
            macros = obj.macros
        return self.visit(obj.body, context=context, macros=macros)

    def visit_GateStatement(self, obj, context=None, macros=None):
        # Note: The code originally checked if a gate was a native gate, macro, or neither,
        # and raised an exception if neither. This assumes everything not a macro is a native gate.
        indices = defaultdict(set)
        if obj.name in macros:
            return self.visit(macros[obj.name].body, {**context, **obj.parameters})
        else:
            # Assumed to be a native gate
            for param in obj.parameters.values():
                self.merge_into(indices, self.visit(param))

    def visit_NamedQubit(self, obj, context=None, macros=None):
        reg, idx = obj.resolve_qubit(context)
        return {reg.name: {idx}}

    def visit_Register(self, obj, context=None, macros=None):
        """Called when a register (or register alias) is an argument to a gate. Jaqal
        does not currently allow this."""
        if obj.size is not None:
            size = obj.size
        else:
            size = obj.resolve_size()
        indices = defaultdict(set)
        for reg, idx in (obj[i].resolve_qubit(context) for i in range(size)):
            indices[reg.name].add(idx)

    def merge_into(self, tgt_dict, src_dict):
        """Merge all values from src_dict into tgt_dict"""
        for key in src_dict:
            tgt_dict[key] |= src_dict[key]
