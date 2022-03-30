# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.

import os
import socket
import json
import math
import select

from jaqalpaq.generator import generate_jaqal_program
from jaqalpaq.core.result import ExecutionResult, RelativeFrequencySubcircuit
from jaqalpaq.error import JaqalError


def run_jaqal_string(jaqal):
    """Run this Jaqal string. This communicates with an existing server."""
    send_jaqal(jaqal)
    return receive_response()


def run_jaqal_file(fname):
    with open(fname, "r") as fd:
        return run_jaqal_string(fd.read())


def run_jaqal_circuit(circ):
    jaqal = generate_jaqal_program(circ)
    return run_jaqal_string(jaqal)


def send_jaqal(jaqal):
    """Send the jaqal text to the host."""
    sock = _get_host_socket()
    sock.send(jaqal.encode())


def receive_response():
    """Wait until we receive a response from the Jaqal we sent."""
    # The response is serialized JSON. Each entry in the array is a measurement
    # in the Jaqal file, and each entry in those entries represents
    sock = _get_host_socket()
    resp_list = []
    polling_timeout = 0.1
    started = False
    while True:
        block_size = 4096  # size recommended by Python docs
        events = select.select([sock], [], [sock], polling_timeout)
        if any(events):
            packet = sock.recv(block_size)
            if packet:
                resp_list.append(packet.decode())
                started = True
                continue

        if started:
            break
    resp_text = "".join(resp_list)

    # Deserialize the JSON into a list of lists of floats
    try:
        results = json.loads(resp_text)
    except Exception as exc:
        print(resp_text)
        raise JaqalError(f"Bad response: {exc}") from exc

    # Validate the format of the returned JSON
    results = validate_response(results)

    qubit_count = math.log2(len(results[0]))
    if 2**qubit_count != len(results[0]):
        import warnings

        warnings.warn("Invalid frequencies")

    # Create a readout and subcircuit for each inner list. This isn't
    # quite right but is good enough for what we're doing.
    subcircuits = []
    for pidx, rfreqs in enumerate(results):
        subcircuits.append(IpcSubcircuit(pidx, qubit_count, rfreqs))

    # Combine into an ExecutionResult object
    er = ExecutionResult(subcircuits)
    return er


def validate_response(results):
    """Make sure the JSON-decoded results from the host have the expected
    format."""
    ret = []
    for sidx, subcirc in enumerate(results):
        probs = [float(p) for p in subcirc]
        if not math.isclose(sum(probs), 1.0):
            raise JaqalError(f"Line {sidx} of results did not sum to 1")
        ret.append(probs)
    return ret


##
# Redefined results classes
#


class IpcSubcircuit(RelativeFrequencySubcircuit):
    def __init__(self, index, qubit_count, relative_frequencies):
        super().__init__(None, index, relative_frequencies=relative_frequencies)
        self._qubit_count = qubit_count

    @property
    def measured_qubits(self):
        return [None for i in range(self._qubit_count)]

    def __repr__(self):
        return f"<{type(self).__name__}>"


##
# Private helper functions
#


def _get_host_socket():
    """Return a socket to communicate with the host, creating it if
    necessary. The host is a singleton and cannot be changed during the
    execution of the program."""

    global _host_socket

    if _host_socket is None:
        address = ("localhost", _get_port())
        try:
            _host_socket = socket.create_connection(address)
        except Exception as exc:
            raise JaqalError(f"Could not connect to host: {exc}")

    return _host_socket


def _get_port():
    """Return the port to connect to the host or raise an exception if it
    has not been configured."""
    port_str = os.environ.get("JAQALPAQ_RUN_PORT")
    if port_str is None:
        raise JaqalError("JAQALPAQ_RUN_PORT must be set")
    try:
        port = int(port_str)
    except ValueError:
        raise JaqalError(
            f"Could not read a port from the value of JAQALPAQ_RUN_PORT: {port_str}"
        )
    return port


# The socket we've been using to send Jaqal code to our host. By using
# a global variable we limit the utility of this module. For more
# advanced uses, the Jaqal Application Framework may be useful.
_host_socket = None
