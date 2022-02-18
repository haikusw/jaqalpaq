# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
from jaqalpaq.parser import parse_jaqal_file, parse_jaqal_string
from jaqalpaq.core.algorithm import expand_macros, fill_in_let, expand_subcircuits
from .unitary import UnitarySerializedEmulator


def run_jaqal_circuit(circuit, backend=None):
    """Execute a Jaqal :class:`~jaqalpaq.core.Circuit` in a noiseless emulator.

    :param Circuit circuit: The Jaqalpaq circuit to be run.
    :param backend: The backend to perform the circuit simulation/emulation.
        Defaults to UnitarySerializedEmulator.

    :rtype: ExecutionResult

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    if backend is None:
        backend = UnitarySerializedEmulator()

    expanded = expand_macros(fill_in_let(expand_subcircuits(circuit)))
    return backend(expanded).execute()


def run_jaqal_string(jaqal, backend=None):
    """Execute a Jaqal string in a noiseless emulator.

    :param str jaqal: The literal Jaqal program text.
    :param backend: The backend to perform the circuit simulation/emulation.
        Defaults to UnitarySerializedEmulator.

    :rtype: ExecutionResult

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    return run_jaqal_circuit(parse_jaqal_string(jaqal, autoload_pulses=True), backend)


def run_jaqal_file(fname, backend=None):
    """Execute a Jaqal program in a file in a noiseless emulator.

    :param str fname: The path to a Jaqal file to execute.
    :param backend: The backend to perform the circuit simulation/emulation.
        Defaults to UnitarySerializedEmulator.

    :rtype: ExecutionResult

    .. note::
        Random seed is controlled by numpy.random.seed.  Consider calling ::

            numpy.random.seed(int(time.time()))

        for random behavior.

    """
    return run_jaqal_circuit(parse_jaqal_file(fname, autoload_pulses=True), backend)


__all__ = [
    "run_jaqal_string",
    "run_jaqal_file",
    "run_jaqal_circuit",
]
