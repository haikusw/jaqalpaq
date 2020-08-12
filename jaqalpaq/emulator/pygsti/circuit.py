# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from collections import defaultdict
import numpy as np

import pygsti
import pygsti.objects

from jaqalpaq import JaqalError
from jaqalpaq.core import Macro
from jaqalpaq.core.constant import Constant
from jaqalpaq.core.algorithm.used_qubit_visitor import UsedQubitIndicesVisitor
from jaqalpaq.core.algorithm.walkers import TraceSerializer

from .model import build_noiseless_native_model
from jaqalpaq.emulator.backend import IndependentSubcircuitsBackend


def pygsti_label_from_statement(gate):
    """Generate a pyGSTi label appropriate for a Jaqal gate

    :param gate: A Jaqal gate object
    :return: A pyGSTi Label object

    """
    args = [f"G{gate.name.lower()}"]
    for param, template in zip(gate.parameters.values(), gate.gate_def.parameters):
        if template.classical:
            args.append(";")
            if type(param) == Constant:
                args.append(param.value)
            else:
                args.append(param)
        else:
            args.append(param.name)
    return pygsti.objects.Label(args)


def pygsti_circuit_from_gatelist(gates, registers):
    """Generate a pyGSTi circuit from a list of Jaqal gates, and the associated registers.

    :param gates: An iterable of Jaqal gates
    :param registers: An iterable of fundamental registers
    :return: A pyGSTi Circuit object

    All lets must have been resolved, and all macros must have been expanded at this point.

    """
    lst = []
    start = False
    end = False
    for gate in gates:
        if gate.name not in ["prepare_all", "measure_all"]:
            lst.append(pygsti_label_from_statement(gate))
        else:
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

    return pygsti.objects.Circuit(
        lst, line_labels=[qubit.name for reg in registers for qubit in reg]
    )


class UnitarySerializedEmulator(IndependentSubcircuitsBackend):
    """Serialized emulator using pyGSTi circuit objects

    This object should be treated as an opaque symbol to be passed to run_jaqal_circuit.
    """

    def _probability(self, trace):
        """Generate the probabilities of outcomes of a subcircuit

        :param Trace trace: the subcircut of circ to generate probabilities for
        :return: A pyGSTi outcome dictionary.
        """

        circ = self.circuit
        s = TraceSerializer(trace)
        pc = pygsti_circuit_from_gatelist(
            list(s.visit(circ)), circ.fundamental_registers()
        )
        model = build_noiseless_native_model(circ.registers, circ.native_gates)
        probs = np.array([(int(k[0][::-1], 2), v) for k, v in model.probs(pc).items()])
        return probs[probs[:, 0].argsort()][:, 1].copy()


class NoisyVisitor(UsedQubitIndicesVisitor):
    validate_parallel = True

    def __init__(self, get_operation, make_idle):
        self.get_operation = get_operation
        self.make_idle = make_idle

    def visit_LoopStatement(self, obj, context=None):
        operation, indices, duration = self.visit(obj.statements, context=context)
        return (
            pygsti.objects.ComposedOp([operation] * obj.iterations),
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
            operation = pygsti.objects.ComposedOp(
                [
                    pygsti.objects.ComposedOp(
                        [branch[0]]
                        + [
                            pygsti.objects.EmbeddedOp(
                                [self.labels(self.all_qubits)],
                                [idx],
                                self.make_idle(duration - branch[2]),
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
                            pygsti.objects.EmbeddedOp(
                                [self.labels(self.all_qubits)],
                                [idx],
                                self.make_idle(sub_duration),
                            )
                        )
            return (pygsti.objects.ComposedOp(operations), indices, duration)

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
            op = self.get_operation(
                obj.name,
                [obj.parameters[v.name] for v in obj.gate_def.classical_parameters],
            )
            op = pygsti.objects.EmbeddedOp(
                self.labels(self.all_qubits), self.labels(indices), op
            )
            return (op, indices, 1)
