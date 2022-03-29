# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.

import os

from jaqalpaq.error import JaqalError

# We use environment variables to alter the behavior of these functions.
#
# JAQALPAQ_RUN_EMULATOR -- If this environment variable is set and has
# a value starting with '1', 't', or 'T', then use the emulator
# unconditionally.
#
# JAQALPAQ_RUN_PORT -- If This variable is set, and
# JAQALPAQ_RUN_EMULATOR does not indicate to use the emulator,
# communicate with another process over a local tcp socket on the
# given port.


def run_jaqal_circuit(circuit, emulator_backend=None):
    """Execute a Jaqal :class:`~jaqalpaq.core.Circuit` using either an
    emulator or by communicating over IPC with another process.
    :param Circuit circuit: The Jaqalpaq circuit to be run.
    :param emulator_backend: The backend to perform the circuit simulation/emulation.
        Defaults to UnitarySerializedEmulator.
        Ignored if not using the emulator.

    :rtype: ExecutionResult

    .. note::
        See :module:`jaqalpaq.emulator.frontend`

    """

    runner_type, runner_port = _get_runner()
    if runner_type == "emulator":
        import jaqalpaq.emulator

        return jaqalpaq.emulator.run_jaqal_circuit(circuit, backend=emulator_backend)
    elif runner_type == "ipc":
        import jaqalpaq.ipc.ipc

        return jaqalpaq.ipc.ipc.run_jaqal_circuit(circuit)
    else:
        raise JaqalError("Internal error: unknown runner")


def run_jaqal_string(jaqal, emulator_backend=None):
    """Execute a Jaqal :class:`~jaqalpaq.core.Circuit` using either an
    emulator or by communicating over IPC with another process.
    :param str jaqal: The literal Jaqal program text.
    :param emulator_backend: The backend to perform the circuit simulation/emulation.
        Defaults to UnitarySerializedEmulator.
        Ignored if not using the emulator.

    :rtype: ExecutionResult

    .. note::
        See :module:`jaqalpaq.emulator.frontend`

    """

    runner_type, runner_port = _get_runner()
    if runner_type == "emulator":
        import jaqalpaq.emulator

        return jaqalpaq.emulator.run_jaqal_string(jaqal, backend=emulator_backend)
    elif runner_type == "ipc":
        import jaqalpaq.ipc.ipc

        return jaqalpaq.ipc.ipc.run_jaqal_string(jaqal)
    else:
        raise JaqalError("Internal error: unknown runner")


def run_jaqal_file(fname, emulator_backend=None):
    """Execute a Jaqal :class:`~jaqalpaq.core.Circuit` using either an
    emulator or by communicating over IPC with another process.
    :param str fname: The path to a Jaqal file to execute.
    :param emulator_backend: The backend to perform the circuit simulation/emulation.
        Defaults to UnitarySerializedEmulator.
        Ignored if not using the emulator.

    :rtype: ExecutionResult

    .. note::
        See :module:`jaqalpaq.emulator.frontend`

    """

    runner_type, runner_port = _get_runner()
    if runner_type == "emulator":
        import jaqalpaq.emulator

        return jaqalpaq.emulator.run_jaqal_file(fname, backend=emulator_backend)
    elif runner_type == "ipc":
        import jaqalpaq.ipc.ipc

        return jaqalpaq.ipc.ipc.run_jaqal_file(fname)
    else:
        raise JaqalError("Internal error: unknown runner")


def _get_runner():
    """Return whether we should use the emulator or ipc, and if the
    latter, what port to use."""
    if os.environ.get("JAQALPAQ_RUN_EMULATOR", "").startswith(("1", "t", "T")):
        return "emulator", None
    try:
        port = int(os.environ["JAQALPAQ_RUN_PORT"])
    except:
        return "emulator", None
    else:
        return "ipc", port
