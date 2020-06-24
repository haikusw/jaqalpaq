import pygsti
import pygsti.objects

import numpy as np
from jaqalpaq import JaqalError
from jaqalpaq.core.constant import Constant


def pygsti_label_from_statement(gate):
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


def pygsti_circuit_from_code(qsc):
    lst = []
    start = False
    end = False
    for moment in qsc.body.moment_iter():
        for gate in moment:
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
        lst,
        line_labels=[
            qubit.name for reg in qsc.fundamental_registers() for qubit in reg
        ],
    )
