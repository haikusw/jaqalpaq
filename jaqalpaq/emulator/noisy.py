# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from collections import defaultdict

from jaqalpaq.core import Macro
from jaqalpaq.error import JaqalError
from jaqalpaq.core.algorithm.visitor import Visitor
from jaqalpaq.core.algorithm.walkers import TraceVisitor, DiscoverSubcircuits
from jaqalpaq.core.algorithm.used_qubit_visitor import UsedQubitIndicesVisitor
from .noisy_gate_model import get_operation, make_idle

from pygsti.objects import ComposedOp, EmbeddedOp


class NoisyVisitor(UsedQubitIndicesVisitor):
    validate_parallel = True

    def visit_LoopStatement(self, obj, context=None):
        operation, indices, duration = self.visit(obj.statements, context=context)
        return (
            ComposedOp([operation] * obj.iterations),
            indices,
            duration * obj.iterations,
        )
        # Use "repeated op" in next version of pygsti when we update to it.

    def visit_BlockStatement(self, obj, context=None):
        visitor = UsedQubitIndicesVisitor()
        visitor.all_qubits = self.all_qubits
        indices = visitor.visit(obj, context=context)
        if obj.parallel:
            branches = [self.visit(sub_obj, context=context) for sub_obj in obj]
            duration = max([branch[2] for branch in branches])
            operation = ComposedOp(
                [
                    ComposedOp(
                        [branch[0]]
                        + [
                            EmbeddedOp(
                                [self.labels(self.all_qubits)],
                                [idx],
                                make_idle(duration - branch[2]),
                            )
                            for idx in self.labels(branch[1])
                        ]
                    )
                    for branch in branches
                ]
            )
            return (operation, indices, duration)
        else:
            operations = []
            duration = 0
            for sub_obj in obj:
                sub_operation, sub_indices, sub_duration = self.visit(
                    sub_obj, context=context
                )
                if sub_operation is None:
                    continue
                duration += sub_duration
                operations.append(sub_operation)
                for idx in self.labels(indices):
                    if idx not in self.labels(sub_indices):
                        operations.append(
                            EmbeddedOp(
                                [self.labels(self.all_qubits)],
                                [idx],
                                make_idle(sub_duration),
                            )
                        )
            return (ComposedOp(operations), indices, duration)

    def labels(self, indices):
        return ["Q" + k + str(v) for k in indices for v in indices[k]]

    def visit_GateStatement(self, obj, context=None):
        # Note: The code originally checked if a gate was a native gate, macro, or neither,
        # and raised an exception if neither. This assumes everything not a macro is a native gate.
        indices = defaultdict(set)
        # Note: This could be more elegant with a is_macro method on gates
        if isinstance(obj.gate_def, Macro):
            context = context or {}
            macro_context = {**context, **obj.parameters}
            macro_body = obj.gate_def.body
            return self.visit(macro_body, macro_context)
        else:
            for param in obj.used_qubits:
                if param is all:
                    self.merge_into(indices, self.all_qubits)
                    return (None, indices, 0)
                else:
                    self.merge_into(indices, self.visit(param, context=context))
            op = get_operation(
                obj.name,
                [obj.parameters[v.name] for v in obj.gate_def.classical_parameters],
            )
            op = EmbeddedOp(self.labels(self.all_qubits), self.labels(indices), op)
            return (op, indices, 1)
