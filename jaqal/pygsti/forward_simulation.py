import pygsti
import numpy as np
import scipy
from .pygstimodel import build_noiseless_native_model
from .frontend import pygsti_circuit_from_code


def forward_simulate_circuit(
    circuit, model=None, qubit_label_func=lambda qidx: "q[{}]".format(qidx)
):
    assert (
        circuit.macros == {}
    ), "Jaqal macros currently unsupported for forward simulation.  Please unroll Jaqal circuit first."
    num_qubits = np.sum(
        [circuit.registers[key].size for key in circuit.registers.keys()]
    )
    if model is None:
        model = build_noiseless_native_model(num_qubits, qubit_label_func)
    pygsti_circuit = pygsti_circuit_from_code(circuit)
    probs = model.probs(pygsti_circuit)
    return probs


def forward_simulate_circuit_counts(
    jaqal_circ,
    N,
    model=None,
    qubit_label_func=lambda qidx: "q[{}]".format(qidx),
    tol=1e-10,
):
    probs = forward_simulate_circuit(
        jaqal_circ, model=model, qubit_label_func=qubit_label_func
    )
    for item in probs.items():
        if (item[1] < 0) and (np.abs(item[1]) < tol):
            probs[item[0]] = 0
        elif (item[1] > 1) and (item[1] < 1 + tol):
            probs[item[0]] = 1
    counts = np.random.multinomial(N, list(probs.values()))
    counts_dict = {}
    for key_idx, key in enumerate(probs.keys()):
        counts_dict[key] = counts[key_idx]
    return counts_dict
