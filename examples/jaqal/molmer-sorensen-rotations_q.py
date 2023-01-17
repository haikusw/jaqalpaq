from jaqalpaq.qsyntax import circuit


@circuit
def molmer_sorensen_rotations(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(2, name="q")
    with Q.subcircuit():
        Q.MS(q[0], q[1], 0.123, 0.987)
    with Q.subcircuit():
        Q.Px(q[0])
        Q.MS(q[0], q[1], 0.123, 0.987)
