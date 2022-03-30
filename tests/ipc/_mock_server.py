import socket, select, os
import json
from jaqalpaq.emulator import run_jaqal_string

BLOCK_SIZE = 4096  # size recommended by Python docs
POLLING_TIMEOUT = 0.1

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind("/tmp/ipc_test")
try:
    server.listen(1)
    conn, addr = server.accept()

    resp_list = []
    started = False
    while True:
        events = select.select([conn], [], [conn], POLLING_TIMEOUT)
        if any(events):
            packet = conn.recv(BLOCK_SIZE)
            if packet:
                resp_list.append(packet.decode())
                started = True
                continue

        if started:
            break
    resp_text = "".join(resp_list)

    # Unvalidated and unauthenticated network-received data is being passed to
    # the Jaqal emulator here.
    exe_res = run_jaqal_string(resp_text)

    results = [list(subcirc.probability_by_int) for subcirc in exe_res.subcircuits]

    conn.send(json.dumps(results).encode())
    server.close()
finally:
    os.unlink("/tmp/ipc_test")
