# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from collections import defaultdict

import pygsti
from pygsti.baseobjs import Label, CircuitLabel
from pygsti.circuits import Circuit

from jaqalpaq.error import JaqalError
from jaqalpaq.core import Macro
from jaqalpaq.core.constant import Constant
from jaqalpaq.core.gatedef import IdleGateDefinition
from jaqalpaq.core.algorithm.used_qubit_visitor import UsedQubitIndicesVisitor


def pygsti_label_from_statement(gate, n_qubits):
    """Generate a pyGSTi label appropriate for a Jaqal gate

    :param gate: A Jaqal gate object
    :return: A pyGSTi Label object

    """
    if isinstance(gate.gate_def, IdleGateDefinition):
        return None

    args = [f"GJ{gate.name}"]
    for param, template in zip(gate.parameters.values(), gate.gate_def.parameters):
        if template.classical:
            args.append(";")
            if type(param) == Constant:
                args.append(param.value)
            else:
                args.append(param)
        else:
            # quantum argument: a qubit
            args.append(n_qubits - param.alias_index - 1)
    return Label(args)


def pygsti_circuit_from_gatelist(gates, n_qubits):
    """Generate a pyGSTi circuit from a list of Jaqal gates.

    :param gates: An iterable of Jaqal gates
    :param n_qubits: The number of qubits.
    :return: A pyGSTi Circuit object

    All lets must have been resolved, and all macros must have been expanded at this point.

    """
    lst = []
    start = False
    end = False
    for gate in gates:
        if gate.name == "prepare_all":
            if not start:
                start = True
            else:
                assert False, "You can't start a circuit twice!"
        elif gate.name == "measure_all":
            if not end:
                end = True
            else:
                assert False, "You can't end a circuit twice!"
        else:
            label = pygsti_label_from_statement(gate, n_qubits)
            if label is not None:
                lst.append(label)

    return Circuit(lst, line_labels=list(range(n_qubits)))


def pygsti_circuit_from_circuit(circuit, **kwargs):
    visitor = pyGSTiCircuitGeneratingVisitor(**kwargs)
    return visitor.visit(circuit)


class pyGSTiCircuitGeneratingVisitor(UsedQubitIndicesVisitor):
    validate_parallel = True

    def __init__(self, *args, durations=None, n_qubits=None, **kwargs):
        self.durations = durations
        self.n_qubits = n_qubits
        super().__init__(**kwargs)

    def idle_gate(self, indices, duration, parallel=None):
        labels = self.labels(indices)
        if len(labels) == 0:
            return parallel

        if parallel is None:
            ops = []
        else:
            ops = [parallel]

        for lbl in labels:
            ops.append(Label(("Gidle", lbl, ";", duration)))

        return Label(ops)

    def visit_Circuit(self, obj, context=None):
        op, indices, duration = super().visit_Circuit(obj, context=context)
        return Circuit(() if op is None else (op,), line_labels=self.llbls)

    def visit_LoopStatement(self, obj, context=None):
        if not self.started:
            return self.visit(obj.statements, context=context)

        op, indices, duration = self.visit(obj.statements, context=context)
        if op is None:
            return (None, indices, 0)
        n = obj.iterations
        return (CircuitLabel("", (op,), self.llbls, reps=n), indices, duration * n)

    def visit_BlockStatement(self, obj, context=None):
        visitor = UsedQubitIndicesVisitor(trace=self.trace)
        visitor.all_qubits = self.all_qubits
        try:
            llbls = self.llbls
        except AttributeError:
            llbls = self.llbls = self.labels(self.all_qubits)

        indices = visitor.visit(obj, context=context)

        if obj.parallel:
            branches = [
                self.visit(sub_obj, context=context)
                for n, sub_obj in self.trace_statements(obj.statements)
            ]

            if len(branches) == 0:
                return (None, indices, 0)

            duration = max([branch[2] for branch in branches])

            ops = []
            for sub_op, sub_indices, sub_duration in branches:
                idle_dur = duration - sub_duration

                if sub_op is None:
                    if duration > 0:
                        ops.append(self.idle_gate(sub_indices, duration))
                elif idle_dur <= 0:
                    ops.append(sub_op)
                else:
                    ops.append(
                        CircuitLabel(
                            "", (sub_op, self.idle_gate(sub_indices, idle_dur)), llbls
                        )
                    )

            return (Label(ops), indices, duration)
        else:
            ops = []
            duration = 0
            for n, sub_obj in self.trace_statements(obj.statements):
                sub_op, sub_indices, sub_duration = self.visit(sub_obj, context=context)
                if (sub_duration <= 0) and (sub_op is None):
                    continue

                duration += sub_duration

                inv_indices = indices.copy()
                for reg in list(inv_indices.keys()):
                    inv_indices[reg] = inv_indices[reg] - sub_indices[reg]

                ops.append(self.idle_gate(inv_indices, sub_duration, parallel=sub_op))

            if len(ops) == 0:
                return (None, indices, 0)

            return (CircuitLabel("", ops, llbls), indices, duration)

    def labels(self, indices):
        if not indices:
            return []

        if len(indices) > 1:
            raise NotImplementedError("Multiple fundamental registers unsupported.")
        (k,) = indices
        return list(range(len(indices[k])))

    def visit_GateStatement(self, obj, context=None):
        # Note: The code originally checked if a gate was a native gate, macro, or neither,
        # and raised an exception if neither. This assumes everything not a macro is a native gate.
        # Note: This could be more elegant with a is_macro method on gates
        if isinstance(obj.gate_def, Macro):
            assert False
            # This should never be called: we should expand macros before using this.
            context = context or {}
            macro_context = {**context, **obj.parameters}
            macro_body = obj.gate_def.body
            return self.visit(macro_body, macro_context)
        else:
            indices = defaultdict(set)
            if obj.name in ("prepare_all", "measure_all"):
                # Special case handling of prepare/measure
                return (None, indices, 0)

            label = pygsti_label_from_statement(obj, self.n_qubits)
            for param in obj.used_qubits:
                if param is all:
                    self.merge_into(indices, self.all_qubits)
                    # TODO: check prepare_all/measure_all here
                    label = None
                else:
                    self.merge_into(indices, self.visit(param, context=context))
            # TODO: Resolve macros and expand lets within this visitor.
            #       The pygsti_label_from_statement will need to be passed context information.
            if isinstance(obj.gate_def, IdleGateDefinition):
                name = obj.gate_def._parent_def.name
            else:
                name = obj.name

            try:
                duration = self.durations[name]
            except KeyError:
                # default to 0 duration
                return (label, indices, 0)

            return (label, indices, duration(*obj.parameters.values()))
