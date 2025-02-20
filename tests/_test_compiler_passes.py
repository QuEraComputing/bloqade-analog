from bloqade.analog import start
from bloqade.analog.ir import analog_circuit
from bloqade.analog.submission.capabilities import get_capabilities
from bloqade.analog.compiler.passes.hardware import (
    assign_circuit,
    analyze_channels,
    generate_ahs_code,
    validate_waveforms,
    canonicalize_circuit,
)

circuit = (
    start.rydberg.detuning.uniform.piecewise_linear([0.1, 1.2, 0.3], [-10, -10, 10, 10])
    .amplitude.uniform.piecewise_linear([0.1, 1.4, 0.1], [0, 10, 10, 0])
    .parse_circuit()
)

seq2 = start.rydberg.detuning.uniform.piecewise_linear(
    [0.3, 1.2, 0.3], [10, 10, -10, -10]
).parse_sequence()

circuit = analog_circuit.AnalogCircuit(circuit.register, circuit.sequence.append(seq2))

assignments = {}
capabilities = get_capabilities()


level_couplings = analyze_channels(circuit)
circuit = canonicalize_circuit(circuit, level_couplings)
circuit = assign_circuit(circuit, assignments)
validate_waveforms(level_couplings, circuit)
ahs_code = generate_ahs_code(capabilities, level_couplings, circuit)
# 7. specialize to QuEra/Braket IR
quera_ir, parallel_decoder = ahs_code.generate_quera_ir(shots=100)
braket_ir, parallel_decoder = ahs_code.generate_braket_ir(shots=100)
print(quera_ir.effective_hamiltonian.rydberg.rabi_frequency_amplitude.global_)
