import pygsti
import numpy as np
import scipy


class XRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=4, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 1
        theta = float(args[0])
        superop = pygsti.unitary_to_pauligate(
            scipy.linalg.expm(-1j / 2 * theta * pygsti.sigmax)
        )
        return pygsti.obj.StaticDenseOp(
            superop
        )  # Should we us DenseOp instead of StaticDenseOp?


class YRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=4, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 1
        theta = float(args[0])
        superop = pygsti.unitary_to_pauligate(
            scipy.linalg.expm(-1j / 2 * theta * pygsti.sigmay)
        )
        return pygsti.obj.StaticDenseOp(
            superop
        )  # Should we us DenseOp instead of StaticDenseOp?


class ZRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=4, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 1
        theta = float(args[0])
        superop = pygsti.unitary_to_pauligate(
            scipy.linalg.expm(-1j / 2 * theta * pygsti.sigmaz)
        )
        return pygsti.obj.StaticDenseOp(
            superop
        )  # Should we us DenseOp instead of StaticDenseOp?


class RRotationOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=4, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 2
        phi = float(args[0])  # Axis-angle (in X-Y plane, ccw from +x axis)
        theta = float(args[1])  # Rotation angle.
        superop = pygsti.unitary_to_pauligate(
            scipy.linalg.expm(
                -1j
                / 2
                * theta
                * (np.cos(theta) * pygsti.sigmax + np.sin(theta) * pygsti.sigmay)
            )
        )
        return pygsti.obj.StaticDenseOp(
            superop
        )  # Should we us DenseOp instead of StaticDenseOp?


class MSOpFactory(pygsti.obj.OpFactory):
    def __init__(self):
        pygsti.obj.OpFactory.__init__(self, dim=16, evotype="densitymx")

    def create_object(self, args=None, sslbls=None):
        assert (
            sslbls is None
        )  # don't worry about sslbls for now -- these are for factories that can create gates placed at arbitrary circuit locations
        assert len(args) == 2
        phi = float(args[0])  # Axis-angle (in X-Y plane, ccw from +x axis)
        theta = float(args[1])  # Rotation angle.
        loc_gen = np.cos(phi) * pygsti.sigmax + np.sin(phi) * pygsti.sigmay
        gen = np.kron(loc_gen, loc_gen)
        superop = pygsti.unitary_to_pauligate(scipy.linalg.expm(-1j / 2 * theta * gen))
        return pygsti.obj.StaticDenseOp(
            superop
        )  # Should we us DenseOp instead of StaticDenseOp?


def build_noiseless_native_model(
    num_qubits, qubit_label_func=lambda qidx: "q[{}]".format(qidx)
):

    # THIS CODE IS NOT OPTIMIZED* BUT IT SHOULD STILL RUN PERFECTLY FINE FOR n<=5 QUBITS.
    # *At the very least we can switch to unitary parameterizations.

    target_model = pygsti.construction.build_localnoise_model(
        nQubits=num_qubits,
        gate_names=[
            "Gprepareall",
            "Gmeasure_all",
            "Gpx",
            "Gpy",
            "Gpz",
            "Gsx",
            "Gsy",
            "Gsz",
            "Gsxd",
            "Gsyd",
            "Gszd",
            "Gsxx",
        ],
        nonstd_gate_unitaries={
            "Gprepareall": np.identity(4),
            "Gmeasure_all": np.identity(4),
            "Gpx": pygsti.sigmax,
            "Gpy": pygsti.sigmay,
            "Gpz": pygsti.sigmaz,
            "Gsx": scipy.linalg.expm(-1j / 4 * np.pi * pygsti.sigmax),
            "Gsy": scipy.linalg.expm(-1j / 4 * np.pi * pygsti.sigmay),
            "Gsz": scipy.linalg.expm(-1j / 4 * np.pi * pygsti.sigmaz),
            "Gsxd": scipy.linalg.expm(1j / 4 * np.pi * pygsti.sigmax),
            "Gsyd": scipy.linalg.expm(1j / 4 * np.pi * pygsti.sigmay),
            "Gszd": scipy.linalg.expm(1j / 4 * np.pi * pygsti.sigmaz),
            "Gsxx": scipy.linalg.expm(
                -1j / 2 * np.pi * np.kron(pygsti.sigmax, pygsti.sigmax)
            ),
        },
        availability={"Gsxx": "all-permutations"},
        #            qubit_labels=['q[{}]'.format(i) for i in range(num_qubits)])
        qubit_labels=[qubit_label_func(qidx) for qidx in range(num_qubits)],
    )

    aux_qubit_labels = ["Q{}".format(qidx) for qidx in range(num_qubits)]

    Grx_factory = XRotationOpFactory()
    Gry_factory = YRotationOpFactory()
    Grz_factory = ZRotationOpFactory()
    Gr_factory = RRotationOpFactory()
    Gms_factory = MSOpFactory()

    #    qubit_labels = ('q[{}]'.format(i) for i in range(3))

    for qidx_0 in range(num_qubits):
        target_model.factories["layers"][
            ("Grx", qubit_label_func(qidx_0))
        ] = pygsti.obj.EmbeddedOpFactory(
            aux_qubit_labels, (aux_qubit_labels[qidx_0],), Grx_factory, dense=True
        )
        target_model.factories["layers"][
            ("Gry", qubit_label_func(qidx_0))
        ] = pygsti.obj.EmbeddedOpFactory(
            aux_qubit_labels, (aux_qubit_labels[qidx_0],), Gry_factory, dense=True
        )
        target_model.factories["layers"][
            ("Grz", qubit_label_func(qidx_0))
        ] = pygsti.obj.EmbeddedOpFactory(
            aux_qubit_labels, (aux_qubit_labels[qidx_0],), Grz_factory, dense=True
        )
        target_model.factories["layers"][
            ("Gr", qubit_label_func(qidx_0))
        ] = pygsti.obj.EmbeddedOpFactory(
            aux_qubit_labels, (aux_qubit_labels[qidx_0],), Gr_factory, dense=True
        )
        for qidx_1 in range(num_qubits):
            if qidx_0 != qidx_1:
                target_model.factories["layers"][
                    ("Gms", qubit_label_func(qidx_0), qubit_label_func(qidx_1))
                ] = pygsti.obj.EmbeddedOpFactory(
                    aux_qubit_labels,
                    (aux_qubit_labels[qidx_0], aux_qubit_labels[qidx_1]),
                    Gms_factory,
                    dense=True,
                )

    return target_model


#    print(type(jaqal_model_0))
#    print_implicit_model_blocks(jaqal_model_0, showSPAM=True)
