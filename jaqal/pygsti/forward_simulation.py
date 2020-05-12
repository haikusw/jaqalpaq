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
