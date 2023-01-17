from math import pi

from jaqalpaq.qsyntax import circuit


def hadamard(Q, target):
    """A Hadamard gate can be implemented as a PI/2 rotation around Y
    followed by a PI rotation around X."""
    Q.R(target, pi / 2, pi / 2)
    Q.R(target, 0, pi)


def cnot(Q, control, target):
    """CNOT implementation from Maslov (2017)"""
    Q.R(control, pi / 2, pi / 2)
    Q.MS(control, target, 0, pi / 2)
    # we can perform these in parallel
    with Q.parallel():
        Q.R(control, 0, -pi / 2)
        Q.R(target, 0, -pi / 2)
    Q.R(control, pi / 2, -pi / 2)


@circuit
def bell_prep(Q):
    q = Q.register(2, name="q")
    Q.usepulses("qscout.v1.std")
    with Q.subcircuit():
        hadamard(Q, q[0])
        cnot(Q, q[0], q[1])
        Q.Px(q[0])

    with Q.subcircuit():
        hadamard(Q, q[0])
        cnot(Q, q[0], q[1])
        cnot(Q, q[0], q[1])
        hadamard(Q, q[0])
