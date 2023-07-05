from bloqade import start

import numpy as np
from bokeh.plotting import figure, show

durations = ["ramp_time", "run_time", "ramp_time"]

rabi_oscillations_program = (
    start.add_position((0, 0))
    .rydberg.rabi.amplitude.uniform.piecewise_linear(
        durations=durations, values=[0, "rabi_value", "rabi_value", 0]
    )
    .detuning.uniform.piecewise_linear(
        durations=durations, values=[0, "detuning_value", "detuning_value", 0]
    )
)

rabi_oscillation_job = rabi_oscillations_program.assign(
    ramp_time=0.06, rabi_value=15, detuning_value=0.0
).batch_assign(run_time=np.around(np.arange(0, 21, 1) * 0.05, 13))

# Simulation Results
emu_job = rabi_oscillation_job.braket_local_simulator(10000).submit().report()

# HW results
hw_job = (
    rabi_oscillation_job.parallelize(24)
    .braket(100)
    .submit()
    .save_json("example-1a-rabi-job.json")
)

p = figure(
    x_axis_label="Time (us)",
    y_axis_label="Rydberg Density",
    toolbar_location="right",
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

p.axis.axis_label_text_font_size = "15pt"
p.axis.major_label_text_font_size = "10pt"

p.line(
    np.around(np.arange(0, 21, 1) * 0.05, 13),
    emu_job.rydberg_densities()[0].to_list(),
    line_width=2,
)

show(p)
