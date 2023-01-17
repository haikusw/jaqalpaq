from jaqalpaq.qsyntax import circuit


@circuit
def Sxx_circuit(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(2, name="q")
    with Q.subcircuit():
        Q.Sxx(q[1], q[0])
