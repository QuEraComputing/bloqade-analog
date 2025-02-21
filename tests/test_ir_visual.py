import itertools

from bokeh.io import save
from bokeh.models import Span
from bokeh.layouts import row
from bokeh.palettes import Dark2_5

from bloqade.analog.visualization.ir_visualize import (
    Field_wvfm,
    SpacialMod,
    mock_data,
    mock_register,
    assemble_field,
    assemble_sequences,
    assemble_pulse_panel,
)


def test_mock_data():
    shared_indicator = Span(dimension="height")

    ## Rydberg:
    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p1 = assemble_field(cube, fig, "Detuning Fields")

    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p2 = assemble_field(cube, fig, "Rabi amp Fields")

    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p3 = assemble_field(cube, fig, "Rabi phase Fields")

    Panel_Pulse1 = assemble_pulse_panel([p1, p2, p3], "Rydberg")

    shared_indicator = Span(dimension="height")

    ## Hyperfine:
    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p1 = assemble_field(cube, fig, "Detuning Fields")

    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p2 = assemble_field(cube, fig, "Rabi amp Fields")

    dats, names, spinfo = mock_data(10)
    fig = Field_wvfm(
        colors=itertools.cycle(Dark2_5),
        data_sources=dats,
        ch_names=names,
        crx_hair_overlay=shared_indicator,
    )
    cube = SpacialMod(spinfo)
    p3 = assemble_field(cube, fig, "Rabi phase Fields")

    Panel_Pulse2 = assemble_pulse_panel([p1, p2, p3], "Hyperfine")

    Seq = assemble_sequences([Panel_Pulse1, Panel_Pulse2])

    save(row(Seq, mock_register()))
