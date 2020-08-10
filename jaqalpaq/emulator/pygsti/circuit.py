# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import numpy as np

import pygsti
import pygsti.objects

from jaqalpaq import JaqalError
from jaqalpaq.core.constant import Constant
from jaqalpaq.core.algorithm.walkers import TraceSerializer

from .model import build_noiseless_native_model
from jaqalpaq.emulator.backend import IndependentSubcircuitsBackend


def pygsti_label_from_statement(gate):
    """Generate a pyGSTi label appropriate for a Jaqal gate

    :param gate: A Jaqal gate object
    :return: A pyGSTi Label object

    """
    name = "G" + gate.name.lower()
    qubits = []
    args = []
    for param, template in zip(gate.parameters.values(), gate.gate_def.parameters):
        if template.classical:
            if type(param) == Constant:
                args.append(param.value)
            else:
                args.append(param)
        else:
            qubits.append(param.name)
    return pygsti.objects.Label(name, qubits, args=args if args else None)


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
        s.visit(circ)
        pc = pygsti_circuit_from_gatelist(s.serialized, circ.fundamental_registers())
        model = build_noiseless_native_model(circ.registers, circ.native_gates)
        probs = np.array([(int(k[0][::-1], 2), v) for k, v in model.probs(pc).items()])
        return probs[probs[:, 0].argsort()][:, 1].copy()
