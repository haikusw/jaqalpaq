import pygsti
import pygsti.objects

import numpy as np
from jaqal import JaqalError


def pygsti_label_from_statement(gate):
    name = "G" + gate.name.lower()
    qubits = []
    args = []
    for param, template in zip(gate.parameters.values(), gate.gate_def.parameters):
        if template.classical:
            args.append(param)
        else:
            qubits.append(param.name)
    return pygsti.objects.Label(name, qubits, args=args if args else None)


def pygsti_circuit_from_code(qsc):
    lst = []
    for moment in qsc.body.moment_iter():
        for gate in moment:
            lst.append(pygsti_label_from_qscout_gate(gate))
    return pygsti.objects.Circuit(
        lst,
        line_labels=[
            qubit.name for reg in qsc.fundamental_registers() for qubit in reg
        ],
    )
