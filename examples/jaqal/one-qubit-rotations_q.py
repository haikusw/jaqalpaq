from jaqalpaq.qsyntax import circuit


@circuit
def one_qubit_rotations(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(1, name="q")

    with Q.subcircuit():
        Q.R(q[0], 0.123, 0.987)
        Q.I_R(q[0], 0.321, 0.4)

    with Q.subcircuit():
        Q.Rx(q[0], 1.234)

    with Q.subcircuit():
        Q.Ry(q[0], 1.234)

    with Q.subcircuit():
        Q.Sx(q[0])
        Q.Rz(q[0], 1.234)
        Q.Sxd(q[0])
        Q.I_Syd(q[0])

    with Q.subcircuit():
        Q.R(q[0], 0.221275, 0.578238)

    with Q.subcircuit():
        Q.Rx(q[0], 0.39544)

    with Q.subcircuit():
        Q.Ry(q[0], 0.321168)
        Q.I_Rz(q[0], 10)

    with Q.subcircuit():
        Q.Sx(q[0])
        Q.Rz(q[0], 0.215873)
        Q.Sxd(q[0])
