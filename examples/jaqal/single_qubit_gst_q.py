from jaqalpaq.qsyntax import circuit

##
# Fiducials
#


def F0(Q, qubit):
    pass


def F1(Q, qubit):
    Q.Sx(qubit)


def F2(Q, qubit):
    Q.Sy(qubit)


def F3(Q, qubit):
    Q.Sx(qubit)
    Q.Sx(qubit)


def F4(Q, qubit):
    Q.Sx(qubit)
    Q.Sx(qubit)
    Q.Sx(qubit)


def F5(Q, qubit):
    Q.Sy(qubit)
    Q.Sy(qubit)
    Q.Sy(qubit)


##
# Germs
#


def G0(Q, qubit):
    Q.Sx(qubit)


def G1(Q, qubit):
    Q.Sy(qubit)


def G2(Q, qubit):
    Q.I_Sx(qubit)


def G3(Q, qubit):
    Q.Sx(qubit)
    Q.Sy(qubit)


def G4(Q, qubit):
    Q.Sx(qubit)
    Q.Sy(qubit)
    Q.I_Sx(qubit)


def G5(Q, qubit):
    Q.Sx(qubit)
    Q.I_Sx(qubit)
    Q.Sy(qubit)


def G6(Q, qubit):
    Q.Sx(qubit)
    Q.I_Sx(qubit)
    Q.I_Sx(qubit)


def G7(Q, qubit):
    Q.Sy(qubit)
    Q.I_Sx(qubit)
    Q.I_Sx(qubit)


def G8(Q, qubit):
    Q.Sx(qubit)
    Q.Sx(qubit)
    Q.I_Sx(qubit)
    Q.Sy(qubit)


def G9(Q, qubit):
    Q.Sx(qubit)
    Q.Sy(qubit)
    Q.Sy(qubit)
    Q.I_Sx(qubit)


def G10(Q, qubit):
    Q.Sx(qubit)
    Q.Sx(qubit)
    Q.Sy(qubit)
    Q.Sx(qubit)
    Q.Sy(qubit)
    Q.Sy(qubit)


@circuit
def single_qubit_gst(Q):
    Q.usepulses("qscout.v1.std")
    q = Q.register(1, name="q")

    with Q.subcircuit():
        F0(Q, q[0])

    with Q.subcircuit():
        F1(Q, q[0])

    with Q.subcircuit():
        F2(Q, q[0])

    with Q.subcircuit():
        F3(Q, q[0])

    with Q.subcircuit():
        F4(Q, q[0])

    with Q.subcircuit():
        F5(Q, q[0])

    with Q.subcircuit():
        F1(Q, q[0])
        F1(Q, q[0])

    with Q.subcircuit():
        F1(Q, q[0])
        F2(Q, q[0])

    with Q.subcircuit():
        F1(Q, q[0])
        with Q.loop(8):
            G1(Q, q[0])
        F1(Q, q[0])
