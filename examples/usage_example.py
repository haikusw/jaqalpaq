import jaqalpaq
from jaqalpaq.parser import parse_jaqal_file
from jaqalpaq.run import run_jaqal_circuit
from jaqalpaq.generator import generate_jaqal_program

JaqalCircuitObject = parse_jaqal_file("jaqal/Sxx_circuit.jaqal")
JaqalCircuitResults = run_jaqal_circuit(JaqalCircuitObject)
print(f"Probabilities: {JaqalCircuitResults.subcircuits[0].probability_by_str}")
JaqalProgram = generate_jaqal_program(JaqalCircuitObject)
