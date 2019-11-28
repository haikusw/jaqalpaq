# QSCOUT High Level Tools
This is the part of QSCOUT's software stack that fits above the QASM level. Everything here should eventually output QASM. This is the place for compilation, compatibility, scheduling, and so forth.
Key components that we should provide:
* One or more higher-level internal representations. (Possibly one scheduled and one unscheduled?)
* The ability to unambiguously output that internal representation to QASM.
* The ability to automatically schedule gates in an efficient (but not necessarily optimal) manner given an unscheduled program.
* The ability to decompose arbitrary unitary operations into native ion-trap gates.
* The ability to convert the data structures used by many other quantum software toolchains to our internal representation.
    * IBM's Qiskit/OpenQASM
    * Rigetti's Quil/pyquil/quilc
    * Google's Cirq
    * Microsoft's Q#
    * ETH Zurich's ProjectQ
    * CQC's t|ket>
* Extensions to some or all of the above toolchains to properly support ion-based quantum computation, as needed.
