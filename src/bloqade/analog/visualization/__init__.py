Use_bokeh = True

if Use_bokeh:
    from typing import List

    from .display import (
        figure_ir,
        display_ir,
        report_figure,
        builder_figure,
        display_report,
        display_builder,
        display_task_ir,
    )
    from .ir_visualize import get_ir_figure, get_field_figure, get_pulse_figure
    from .task_visualize import get_task_ir_figure
    from .atom_arrangement_visualize import (
        get_atom_arrangement_figure,
        assemble_atom_arrangement_panel,
    )
else:
    # display
    def display_ir(obj, assignemnts):
        raise Warning("Bokeh not installed", UserWarning)

    def display_report(report):
        raise Warning("Bokeh not installed", UserWarning)

    def display_task_ir(task_ir):
        raise Warning("Bokeh not installed", UserWarning)

    def display_builder(builder, batch_id):
        raise Warning("Bokeh not installed", UserWarning)

    # visualization
    def get_task_ir_figure(task_ir, **fig_kwargs):
        raise Warning("Bokeh not installed", UserWarning)

    # atom arrangement
    def get_atom_arrangement_figure(
        atom_arng_ir, colors=(), fig_kwargs=None, **assignments
    ):
        raise Warning("Bokeh not installed", UserWarning)

    def assemble_atom_arrangement_panel(atom_arrangement_plots, keys: List[str]):
        raise Warning("Bokeh not installed", UserWarning)

    # ir
    def get_ir_figure(ir, **assignments):
        raise Warning("Bokeh not installed", UserWarning)

    def get_field_figure(ir_field, title, indicator, **assignments):
        raise Warning("Bokeh not installed", UserWarning)

    def get_pulse_figure(ir_pulse, title: str = None, **assginments):
        raise Warning("Bokeh not installed", UserWarning)

    # figure:
    def figure_ir(obj, assignemnts):
        raise Warning("Bokeh not installed", UserWarning)

    def builder_figure(builder, batch_id):
        raise Warning("Bokeh not installed", UserWarning)

    def report_figure(report):
        raise Warning("Bokeh not installed", UserWarning)
