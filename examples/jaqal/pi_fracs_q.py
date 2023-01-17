from jaqalpaq.qsyntax import circuit

from math import pi


@circuit
def empty_loop(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(1, name="q")
    angle0 = Q.let(pi / 32, name="angle0")
    angle1 = Q.let(pi / 16, name="angle1")
    angle2 = Q.let(3 * pi / 32, name="angle2")
    angle3 = Q.let(pi / 8, name="angle3")

    with Q.subcircuit():
        Q.Ry(q[0], angle0)

    with Q.subcircuit():
        Q.Ry(q[0], angle1)

    with Q.subcircuit():
        Q.Ry(q[0], angle2)

    with Q.subcircuit():
        Q.Ry(q[0], angle3)
