import numpy as np

import pygsti
import pygsti.objects

from jaqalpaq import JaqalError
from jaqalpaq.core.constant import Constant
from jaqalpaq.core.algorithm.walkers import SubcircuitSerializer

from .pygstimodel import build_noiseless_native_model


def label_from_statement(gate):
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


def circuit_from_gatelist(gates, registers):
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
            lst.append(label_from_statement(gate))
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
        lst, line_labels=[qubit.name for reg in registers for qubit in reg],
    )


def subexperiment_probabilities(
    circ, subcircuit, noisemodel=build_noiseless_native_model
):
    """Generate the probabilities of outcomes of a subcircuit

    :param circ: The parent circuit
    :param subcircuit: The Subcircuit object describing the portion to generate proba
    :param noisemodel: [undocumented] The method to generate the noisemodel.
    :return: A pyGSTi outcome dictionary.
    """
    s = SubcircuitSerializer(subcircuit)
    s.visit(circ)
    pc = circuit_from_gatelist(s.serialized, circ.fundamental_registers())
    model = noisemodel(circ.registers, circ.native_gates)
    probs = model.probs(pc)
    return probs
