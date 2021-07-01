# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.

import os
import socket
import json
import math
import select

import jaqalpaq.parser
from jaqalpaq.generator import generate_jaqal_program
from jaqalpaq.core.result import (
    Readout,
    Subcircuit,
    ProbabilisticSubcircuit,
    ExecutionResult,
)
from jaqalpaq import JaqalError


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
    # The response is serialized JSON. Each entry in the array is a measurement in the Jaqal file, and each entry in those entries represents
    sock = _get_host_socket()
    resp_list = []
    polling_timeout = 0.1
    started = False
    while True:
        block_size = 4096  # size recommended by Python docs
        events = select.select([sock], [], [sock], polling_timeout)
        if any(events):
            packet = sock.recv(block_size)
            resp_list.append(packet.decode())
            started = True
        elif started:
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

    # Create a readout and subcircuit for each inner list. This isn't
    # quite right but is good enough for what we're doing.
    readouts = []
    subcircuits = []
    for pidx, probs in enumerate(results):
        readout = IpcReadout(None, None, None)
        readouts.append(readout)
        subcircuits.append(IpcSubcircuit(None, pidx, readout, probs))

    # Combine into an ExecutionResult object
    er = ExecutionResult(subcircuits, readouts)
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


class IpcReadout(Readout):
    """Encapsulate the result of measurement of some number of qubits over
    IPC. Ideally this would not differ from readouts generated through
    other means, but IPC does not fully support all features.

    Currently, IPC does not return individual measurement results but
    merely their aggregation over many runs.

    """

    @property
    def index(self):
        raise NotImplementedError()

    @property
    def subcircuit(self):
        raise NotImplementedError()

    @property
    def measured_qubits(self):
        raise NotImplementedError()

    def __repr__(self):
        return f"<{type(self).__name__}>"


class IpcSubcircuit(ProbabilisticSubcircuit):
    def __init__(self, trace, index, readouts, probabilities):
        super().__init__(trace, index, readouts, probabilities)

    @property
    def measured_qubits(self):
        raise NotImplementedError()

    def __repr__(self):
        return f"<{type(self).__name__}>"

    @property
    def probability_by_str(self):
        # This assumes that all probabilities are the same size, which
        # will be true as long as we don't have partial measurements.
        p = self._probabilities
        return OrderedDict([(f"{n:b}"[::-1], v) for n, v in enumerate(p)])


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
            raise JaqalException(f"Could not connect to host: {exc}")

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
