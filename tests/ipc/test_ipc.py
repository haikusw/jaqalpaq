import os, time, sys, subprocess, socket
from contextlib import contextmanager
import unittest, pytest
import numpy

from jaqalpaq.ipc import ipc


@unittest.skipIf(sys.platform.startswith("win"), "IPC tests use Unix sockets")
class IPCTester(unittest.TestCase):
    """Test interacting through the IPC interface."""

    @contextmanager
    def mock_server(self):
        P = subprocess.Popen([sys.executable, "-m", "tests.ipc._mock_server"])

        time.sleep(1)
        ipc._host_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        ipc._host_socket.connect("/tmp/ipc_test")

        try:
            yield
        finally:
            P.send_signal(subprocess.signal.SIGTERM)
            P.communicate()
            ipc._host_socket.close()
            del ipc._host_socket

    def test_bell_prep(self):
        """Run bell_prep.jaqal through the IPC mock server, and parse the results"""

        with self.mock_server():
            exe = ipc.run_jaqal_file("examples/jaqal/bell_prep.jaqal")

        sc1, sc2 = exe.subcircuits
        assert numpy.allclose(sc1.relative_frequency_by_int, [0, 1 / 2, 1 / 2, 0])
        assert numpy.allclose(sc2.relative_frequency_by_int, [1, 0, 0, 0])
