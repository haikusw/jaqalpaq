Changes in 1.1
==============

 - NEW: qscout-gatemodels-ionsim package
   - Microscopic models of gate behavior
 - NEW: Q syntax
   - Simpler interface for writing Jaqal with Python
 - NEW: Subcircuits
   - Encapsulates prepare/measure blocks
 - NEW: JaqalPaw
   - Describes pulses and waveforms used for gates
 - NEW: Reverse transpilers
   - Convert from Qiskit and TKET to Jaqal
 - CHANGED: Default UnitarySerializedEmulator
   - Does not use pyGSTi
   - Faster
   - Provides access to the full unitary of the gates in the circuit
 - CHANGED: Unified Jaqal name space hierarchy
 - CHANGED: Refreshed dependencies on external packages
