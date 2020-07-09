.. _glossary:

JaqalPaq Glossary
=================

.. glossary::

    circuit
        A Jaqal circuit is the full set of Jaqal instructions to be performed by the
        quantum computer, including preparation and measurement calls.  Multiple prepare
        and measure operations may be performed in a circuit.

    flat order
        The flat order of a Jaqal circuit is created by processing and then discarding
        all header statements, expanding all macros, and then stepping through the
        instructions, *ignoring loops*.  In this expanded representation, it is the
        order in which a statement appears, when read.

    readout
        A readout in a Jaqal program occurs when the quantum hardware performs a
        measurement and emits output in the form of the collapsed quantum states of the
        measured qubits.

    subcircuit
        A subcircuit is a collection of statements within a Jaqal circuit that begins with
        the preparation of all qubits in the hardware, and ends with measurement of all
        qubits in the hardware.
