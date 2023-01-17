from jaqalpaq.qsyntax import circuit


@circuit
def nested_bit_flips(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(4, name="q")
    with Q.subcircuit():
        pass

    with Q.subcircuit():
        Q.Px(q[0])

    with Q.subcircuit():
        Q.Px(q[1])

    with Q.subcircuit():
        Q.Px(q[0])
        Q.Px(q[1])

    with Q.subcircuit():
        Q.Px(q[2])

    with Q.subcircuit():
        Q.Px(q[0])
        Q.Px(q[2])

    with Q.subcircuit():
        Q.Px(q[1])
        Q.Px(q[2])

    with Q.subcircuit():
        Q.Px(q[0])
        Q.Px(q[1])
        Q.Px(q[2])

    with Q.subcircuit():
        Q.Px(q[3])

    with Q.subcircuit():
        Q.Px(q[0])
        Q.Px(q[3])

    with Q.subcircuit():
        Q.Px(q[1])
        Q.Px(q[3])

    with Q.subcircuit():
        Q.Px(q[0])
        Q.Px(q[1])
        Q.Px(q[3])

    with Q.subcircuit():
        Q.Px(q[2])
        Q.Px(q[3])

    with Q.subcircuit():
        Q.Px(q[0])
        Q.Px(q[2])
        Q.Px(q[3])

    with Q.subcircuit():
        Q.Px(q[1])
        Q.Px(q[2])
        Q.Px(q[3])
