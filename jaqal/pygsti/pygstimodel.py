import pygsti
import numpy as np
import scipy


def build_noiseless_native_model(
    num_qubits, gates, qubit_label_func=lambda qidx: f"q[{qidx}]",
):
    gate_names = []
    unitaries = {}
    availability = {}

    for g in gates.values():
        name = f"G{g.name.lower()}"
        gate_names.append(name)

        if g.quantum_parameters == 0:
            # AER: We are special casing prepare and measurements right now
            if g.name in ("prepare_all", "measure_all"):
                unitaries[name] = np.identity(2)
            else:
                raise NotImplementedError(f"{g.name} not supported")
            continue

        if g.classical_parameters > 0:
            unitaries[name] = g.ideal_action_pygsti
        else:
            unitaries[name] = g.ideal_action()

        if g.quantum_parameters > 1:
            availability[name] = "all-permutations"

    target_model = pygsti.construction.build_localnoise_model(
        nQubits=num_qubits,
        gate_names=gate_names,
        nonstd_gate_unitaries=unitaries,
        availability=availability,
        qubit_labels=[qubit_label_func(qidx) for qidx in range(num_qubits)],
        parameterization="static unitary",
    )

    return target_model
