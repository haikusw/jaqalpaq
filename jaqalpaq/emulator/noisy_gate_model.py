# Copyright 2020 National Technology & Engineering Solutions of Sandia, LLC (NTESS).
# Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains
# certain rights in this software.
import pygsti
import numpy as np
import qscout.v1.native_gates

num_qubits = 2

# Manually specify error rates if you want different error rates on different gates.
# Also note- we can use more realistic depol model for two-qubit gates.  (Currently 1- and 2-body terms equal weight.)

gate_keys = (
    "R",
    "Rx",
    "Ry",
    "Rz",
    "Px",
    "Py",
    "Pz",
    "Sx",
    "Sy",
    "Sz",
    "Sxd",
    "Syd",
    "Syz",
    "MS",
    "Sxx",
    "I_Sx",
)

depolarization = 1e-3
rotation_error = 1e-2
phase_error = 1e-2

error_dict = {}
for gate_key in gate_keys:
    error_dict[gate_key] = {"depolarization": depolarization}
    if gate_key != "I_Sx":
        error_dict[gate_key]["rotation"] = rotation_error
    if gate_key in ["R", "MS"]:
        error_dict[gate_key]["phase"] = phase_error


class RRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=4, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 2
        phase = float(args[0])
        rotation = float(args[1])

        duration = rotation / (np.pi / 2)

        phase_error = error_dict["R"]["phase"]
        rotation_error = error_dict["R"]["rotation"] * duration
        depolarization_term = (1 - error_dict["R"]["depolarization"]) ** duration

        super_op = pygsti.unitary_to_pauligate(
            qscout.v1.native_gates.U_R(phase + phase_error, rotation + rotation_error)
        ) @ np.diag([1, depolarization_term, depolarization_term, depolarization_term])

        return pygsti.obj.StaticDenseOp(super_op)


class MSRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=16, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 2
        phase = float(args[0])
        rotation = float(args[1])

        duration = (
            10 * rotation / (np.pi / 2)
        )  # Assume MS pi/2 gate 10 times longer than Sx, Sy, Sz

        phase_error = error_dict["MS"]["phase"]
        rotation_error = error_dict["MS"]["rotation"] * duration
        depolarization_term = (1 - error_dict["MS"]["depolarization"]) ** duration

        super_op = pygsti.unitary_to_pauligate(
            qscout.v1.native_gates.U_MS(phase + phase_error, rotation + rotation_error)
        ) @ np.diag([1] + 15 * [depolarization_term])

        return pygsti.obj.StaticDenseOp(super_op)


class RxRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=4, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 1
        rotation = float(args[0])

        duration = rotation / (np.pi / 2)

        rotation_error = error_dict["Rx"]["rotation"] * duration
        depolarization_term = (1 - error_dict["Rx"]["depolarization"]) ** duration

        super_op = pygsti.unitary_to_pauligate(
            qscout.v1.native_gates.U_Rx(rotation + rotation_error)
        ) @ np.diag([1, depolarization_term, depolarization_term, depolarization_term])

        return pygsti.obj.StaticDenseOp(super_op)


class RyRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=4, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 1
        rotation = float(args[0])

        duration = rotation / (np.pi / 2)

        rotation_error = error_dict["Ry"]["rotation"] * duration
        depolarization_term = (1 - error_dict["Ry"]["depolarization"]) ** duration

        super_op = pygsti.unitary_to_pauligate(
            qscout.v1.native_gates.U_Ry(rotation + rotation_error)
        ) @ np.diag([1, depolarization_term, depolarization_term, depolarization_term])

        return pygsti.obj.StaticDenseOp(super_op)


class RzRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=4, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 1
        rotation = float(args[0])

        duration = rotation / (np.pi / 2)

        rotation_error = error_dict["Rz"]["rotation"] * duration
        depolarization_term = (1 - error_dict["Rz"]["depolarization"]) ** duration

        super_op = pygsti.unitary_to_pauligate(
            qscout.v1.native_gates.U_Rz(rotation + rotation_error)
        ) @ np.diag([1, depolarization_term, depolarization_term, depolarization_term])

        return pygsti.obj.StaticDenseOp(super_op)


class I_SzRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=4, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 1
        rotation = float(args[0])

        duration = rotation / (np.pi / 2)

        depolarization_term = (1 - error_dict["I_Sx"]["depolarization"]) ** duration

        super_op = np.diag(
            [1, depolarization_term, depolarization_term, depolarization_term]
        )

        return pygsti.obj.StaticDenseOp(super_op)


Sx = pygsti.unitary_to_pauligate(
    qscout.v1.native_gates.U_Rx(np.pi / 2 + error_dict["Rx"]["rotation"])
) @ np.diag([1] + 3 * [1 - error_dict["Rx"]["depolarization"]])
Sy = pygsti.unitary_to_pauligate(
    qscout.v1.native_gates.U_Ry(np.pi / 2 + error_dict["Ry"]["rotation"])
) @ np.diag([1] + 3 * [1 - error_dict["Ry"]["depolarization"]])
Sz = pygsti.unitary_to_pauligate(
    qscout.v1.native_gates.U_Rz(np.pi / 2 + error_dict["Rz"]["rotation"])
) @ np.diag([1] + 3 * [1 - error_dict["Rz"]["depolarization"]])

Sxd = Sx.T
Syd = Sy.T
Szd = Sz.T

Px = Sx @ Sx
Py = Sy @ Sy
Pz = Sz @ Sz

Sxx = pygsti.unitary_to_pauligate(
    qscout.v1.native_gates.U_MS(
        error_dict["MS"]["phase"], np.pi / 2 + error_dict["MS"]["rotation"]
    )
) @ np.diag([1] + 15 * [1 - error_dict["MS"]["depolarization"]])

all_pairs = [
    (q1, q2) for q1 in range(num_qubits) for q2 in range(num_qubits) if q1 != q2
]

static_gates = {
    "Gsx": Sx,
    "Gsy": Sy,
    "Gsz": Sz,
    "Gsxd": Sxd,
    "Gsyd": Syd,
    "Gszd": Szd,
    "Gpx": Px,
    "Gpy": Py,
    "Gpz": Pz,
    "Gsxx": Sxx,
}

mdl = pygsti.construction.build_localnoise_model(
    nQubits=num_qubits,
    gate_names=list(static_gates.keys()),
    nonstd_gate_unitaries={
        "Gsx": np.identity(2),
        "Gsy": np.identity(2),
        "Gsz": np.identity(2),
        "Gsxd": np.identity(2),
        "Gsyd": np.identity(2),
        "Gszd": np.identity(2),
        "Gpx": np.identity(2),
        "Gpy": np.identity(2),
        "Gpz": np.identity(2),
        "Gsxx": np.identity(4),
    },
    availability={"GSxx": all_pairs},
    parameterization="full",
    independent_gates=True,
)

for gate_name, gate in static_gates.items():
    if gate_name != "Gsxx":
        for q in range(num_qubits):
            mdl.operation_blks["gates"][(gate_name, q)] = gate
    else:
        for q1 in range(num_qubits):
            for q2 in range(num_qubits):
                if q1 != q2:
                    mdl.operation_blks["gates"][(gate_name, q1, q2)] = gate

model_factories = {
    "Gr": RRotationOpFactory(),
    "Grx": RxRotationOpFactory(),
    "Gry": RyRotationOpFactory(),
    "Grz": RzRotationOpFactory(),
    "Gms": MSRotationOpFactory(),
    "Gisx": I_SzRotationOpFactory(),
}

for key in model_factories:
    if key != "Gms":
        for q in range(num_qubits):
            mdl.factories["layers"][(key, q)] = pygsti.obj.EmbeddedOpFactory(
                tuple(range(num_qubits)), (q,), model_factories[key], dense=True
            )
    else:  # Put in all-to-all MS connectivity
        for q1 in range(num_qubits):
            for q2 in range(num_qubits):
                if q1 != q2:
                    mdl.factories["layers"][
                        (key, q1, q2)
                    ] = pygsti.obj.EmbeddedOpFactory(
                        tuple(range(num_qubits)),
                        (q1, q2),
                        model_factories[key],
                        dense=True,
                    )


def get_operation(name, params):
    # if name == "prepare_all" or name == "measure_all":
    if name == "Px":
        return pygsti.obj.StaticDenseOp(Px)
    elif name == "Py":
        return pygsti.obj.StaticDenseOp(Py)
    elif name == "Px":
        return pygsti.obj.StaticDenseOp(Pz)
    elif name == "Sx":
        return pygsti.obj.StaticDenseOp(Sx)
    elif name == "Sy":
        return pygsti.obj.StaticDenseOp(Sy)
    elif name == "Sz":
        return pygsti.obj.StaticDenseOp(Sz)
    elif name == "Szd":
        return pygsti.obj.StaticDenseOp(Szd)
    elif name == "Syd":
        return pygsti.obj.StaticDenseOp(Syd)
    elif name == "Sxd":
        return pygsti.obj.StaticDenseOp(Sxd)
    elif name == "Sxx":
        return pygsti.obj.StaticDenseOp(Sxx)
    elif name == "Rz":
        return RzRotationOpFactory().create_object(params)
    elif name == "Ry":
        return RyRotationOpFactory().create_object(params)
    elif name == "Rx":
        return RxRotationOpFactory().create_object(params)
    elif name == "R":
        return RRotationOpFactory().create_object(params)
    elif name == "MS":
        return MSRotationOpFactory().create_object(params)


def make_idle(duration):
    return I_SzRotationOpFactory().create_object([duration])
