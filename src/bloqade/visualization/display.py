from bokeh.models import Div
from bokeh.layouts import row, column
from bokeh.io import show
from bloqade.visualization import report_visualize
from bokeh.models import (
    NumericInput,
    Button,
    CustomJS,
)


def liner(txt):
    return f"<p>{txt}</p>"


## builder:
def display_builder(analog_circ, metas, batch_id: int):
    kwargs = metas.static_params
    kwargs.update(metas.batch_params[batch_id])

    out = "<p>Assignments: </p>"
    for key, val in kwargs.items():
        out += liner(f" :: {key} = {val}")

    rowobj = analog_circ.figure(**kwargs)

    field = rowobj.children[0]
    reg = rowobj.children[1]
    div = Div(text=out, width=200, height=200)

    show(row(field, column(reg, div)))


## ir
def display_analog_circuit(analog_circuit, assignments):
    show(row(*analog_circuit.figure(**assignments)))


def display_pulse(pulse, assignments):
    show(pulse.figure(**assignments))


def display_sequence(sequence, assignments):
    show(sequence.figure(**assignments))


def display_field(field, assignments):
    show(field.figure(**assignments))


def display_spatialmod(spmod, assignments):
    show(spmod.figure(**assignments))


def display_waveform(wvfm_ir, assignments):
    show(wvfm_ir.figure(**assignments))


def display_atom_arrangement(atom_arrangement, assignments):
    """show the register."""
    p = atom_arrangement.figure(None, **assignments)

    # get the Blocade rad object
    cr = None
    for rd in p.renderers:
        if rd.name == "Brad":
            cr = rd

    # adding rydberg radis input
    Brad_input = NumericInput(
        value=0, low=0, title="Blockade radius (um):", mode="float"
    )

    # js link toggle btn
    toggle_button = Button(label="Toggle")
    toggle_button.js_on_event(
        "button_click",
        CustomJS(args=dict(cr=cr), code="""cr.visible = !cr.visible;"""),
    )

    # js link radius
    Brad_input.js_link("value", cr.glyph, "radius")

    full = column(p, row(Brad_input, toggle_button))
    # full.sizing_mode="scale_both"
    show(full)


## report
def display_report(report):
    dat = report_visualize.format_report_data(report)
    p = report_visualize.report_visual(*dat)
    show(p)


## task_ir
def display_task_lattice(lattice):
    show(lattice.figure())


def display_quera_task_ir(task_ir):
    show(task_ir.figure())


def display_quera_task_rabi_phase(rabi_phase):
    show(rabi_phase.figure())


def display_quera_task_rabi_amp(rabi_amp):
    show(rabi_amp.figure())


def display_quera_task_detuning(detune):
    show(detune.global_figure())
