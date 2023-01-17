from jaqalpaq.qsyntax import circuit


@circuit
def only_idles(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(2, name="q")
    with Q.subcircuit():
        Q.I_Px(q[0])
        Q.I_MS(q[0], q[1], 1, 2)
