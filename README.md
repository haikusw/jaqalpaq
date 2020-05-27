# Python Jaqal Programming Package (JaqalPaq)
This is the part of QSCOUT's software stack that fits above the Jaqal level. Everything here should eventually output Jaqal. This is the place for compilation, compatibility, scheduling, and so forth.
Key components that we should provide:
* One or more higher-level internal representations. (Possibly one scheduled and one unscheduled?)
* The ability to unambiguously output that internal representation to Jaqal.
* The ability to automatically schedule gates in an efficient (but not necessarily optimal) manner given an unscheduled program.
* The ability to decompose arbitrary unitary operations into native ion-trap gates.
* The ability to convert the data structures used by many other quantum software toolchains to our internal representation. Ideally this will include:
    * IBM's Qiskit/OpenQASM
    * Rigetti's Quil/pyquil/quilc
    * Google's Cirq
    * Microsoft's Q#
    * ETH Zurich's ProjectQ
    * CQC's t|ket>
* Extensions to some or all of the above toolchains to properly support ion-based quantum computation, as needed.

To make the software stack as modular as possible, and incidentally also decrease the risk of circular dependencies, we should follow the following philosophy of dependencies:
* Any file at the top-level of the module should depend on only other files at the top-level.
* Any file in the `jaqalpaq.core` submodule can depend on top-level files and other files in `jaqalpaq.core`.
* Any file in another submodule can depend on top-level files, files from `jaqalpaq.core`, and other files in the same submodule.
* Each submodule should function correctly even if every submodule other than that one and `jaqalpaq.core` were removed.
* External dependencies may be required by the `jaqalpaq` package as a whole, or be required by only a single submodule.
For example, each external toolchain's Python API, if one exists, should be required only by the compatibility module for that toolchain; but `numpy` is a reasonable requirement for the package as a whole.
If an external toolchain's Python API is missing, the function of the rest of the software stack should be unaffected.
