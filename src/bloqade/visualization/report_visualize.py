from bokeh.plotting import figure, show
from bokeh.layouts import column, row
from bokeh.models import CustomJS, MultiChoice, Div, HoverTool, Range1d
from bokeh.models import (
    ColumnDataSource,
)

# from bokeh.models import Tabs, TabPanel,, Div, CrosshairTool, Span
from bokeh.palettes import Dark2_5
import math

# import itertools
import numpy as np

# from typing import List


## =====================================================
# below are formatting IR data, and called by IR.


def format_report_data(report):
    # return should be
    # data: List[ColumnDataSources],
    # List[str]:ch_names,
    # spmod_source:ColumnDataSources

    task_tid = report.dataframe.index.get_level_values("task_number").unique()
    task_tid = list(task_tid)

    counts = report.counts
    ryds = report.rydberg_densities()
    assert len(task_tid) == len(counts)

    cnt_sources = []
    ryd_sources = []
    for i, cnt_data in enumerate(counts):
        bitstrings = list(cnt_data.keys())
        cnts = list(cnt_data.values())
        tid = [i] * len(cnts)
        src = ColumnDataSource(
            data=dict(
                tid=tid,
                bitstrings=bitstrings,
                cnts=cnts,
            )
        )

        rydens = list(ryds.iloc[i])
        tid = [i] * len(rydens)

        rsrc = ColumnDataSource(
            data=dict(
                tid=tid,
                sites=[f"{ds}" for ds in range(len(rydens))],
                ryds=rydens,
            )
        )
        cnt_sources.append(src)
        ryd_sources.append(rsrc)

    return cnt_sources, ryd_sources, report.metas, report.name


def mock_data():
    from bloqade.task.base import Geometry

    cnt_sources = []
    ryd_sources = []
    metas = []
    geos = []

    # ===============================
    bitstrings = ["0010", "1101", "1111"]
    cnts = [4, 7, 5]
    tid = [0] * len(cnts)
    src = ColumnDataSource(
        data=dict(
            tid=tid,
            bitstrings=bitstrings,
            cnts=cnts,
        )
    )
    cnt_sources.append(src)
    rsrc = ColumnDataSource(
        data=dict(
            tid=[0, 0, 0, 0],
            sites=["0", "1", "2", "3"],
            ryds=[0.55, 0.45, 0.2, 0.11],
        )
    )
    ryd_sources.append(rsrc)
    metas.append(dict(a=4, b=9, c=10))
    geos.append(
        Geometry(
            sites=[(0.0, 0.0), (0.0, 0.5), (0.5, 0.3), (0.6, 0.7)], filling=[1, 1, 1, 0]
        )
    )

    # ===============================
    bitstrings = ["0101", "1101", "1110", "1111"]
    cnts = [4, 7, 5, 10]
    tid = [1] * len(cnts)
    src = ColumnDataSource(
        data=dict(
            tid=tid,
            bitstrings=bitstrings,
            cnts=cnts,
        )
    )
    cnt_sources.append(src)
    rsrc = ColumnDataSource(
        data=dict(
            tid=[1, 1, 1, 1],
            sites=["0", "1", "2", "3"],
            ryds=[0.33, 0.67, 0.25, 0.34],
        )
    )
    ryd_sources.append(rsrc)
    metas.append(dict(a=10, b=9.44, c=10.3))
    geos.append(
        Geometry(
            sites=[(0.0, 0.1), (0.66, 0.5), (0.3, 0.3), (0.5, 0.7)],
            filling=[1, 0, 1, 0],
        )
    )

    return cnt_sources, ryd_sources, metas, geos, "Mock"


def plot_register(geo):
    """obtain a figure object from the atom arrangement."""
    xs_filled, ys_filled, labels_filled = [], [], []
    xs_vacant, ys_vacant, labels_vacant = [], [], []
    x_min = np.inf
    x_max = -np.inf
    y_min = np.inf
    y_max = -np.inf
    for idx, location_info in enumerate(zip(geo.sites, geo.filling)):
        (x, y), filling = location_info
        x_min = min(x, x_min)
        y_min = min(y, y_min)
        x_max = max(x, x_max)
        y_max = max(y, y_max)
        if filling:
            xs_filled.append(x)
            ys_filled.append(y)
            labels_filled.append(idx)
        else:
            xs_vacant.append(x)
            ys_vacant.append(y)
            labels_vacant.append(idx)

    # Ly = y_max - y_min
    # Lx = x_max - x_min
    # scale_x = (Lx+2)/(Ly+2)

    if len(geo.sites) > 0:
        length_scale = max(y_max - y_min, x_max - x_min, 1)
    else:
        length_scale = 1

    source_filled = ColumnDataSource(
        data=dict(_x=xs_filled, _y=ys_filled, _labels=labels_filled)
    )
    source_vacant = ColumnDataSource(
        data=dict(_x=xs_vacant, _y=ys_vacant, _labels=labels_vacant)
    )
    hover = HoverTool()
    hover.tooltips = [
        ("(x,y)", "(@_x, @_y)"),
        ("index: ", "@_labels"),
    ]

    ## remove box_zoom since we don't want to change the scale

    p = figure(
        width=400,
        height=400,
        tools="wheel_zoom,reset, undo, redo, pan",
        toolbar_location="above",
    )
    p.x_range = Range1d(x_min - 1, x_min + length_scale + 1)
    p.y_range = Range1d(y_min - 1, y_min + length_scale + 1)

    p.circle(
        "_x", "_y", source=source_filled, radius=0.025 * length_scale, fill_alpha=1
    )
    p.circle(
        "_x",
        "_y",
        source=source_vacant,
        radius=0.025 * length_scale,
        fill_alpha=1,
        color="grey",
        line_width=0.2 * length_scale,
    )

    p.add_tools(hover)

    return p


def report_visual(cnt_sources, ryd_sources, metas, geos, name):
    options = [f"task {cnt}" for cnt in range(len(cnt_sources))]

    figs = []
    # select = Select(title="Select Task", options=[])
    multi_choice = MultiChoice(options=[])

    if len(options):
        color1 = Dark2_5[0]
        color2 = Dark2_5[1]
        for taskname, tsrc, trydsrc, meta, geo in zip(
            options, cnt_sources, ryd_sources, metas, geos
        ):
            content = "<p> Assignments: </p>"
            for var, num in meta.items():
                content += f"<p>{var} = {num}</p>"

            div = Div(
                text=content, width=100, height=400, styles={"overflow-y": "scroll"}
            )

            p = figure(
                x_range=tsrc.data["bitstrings"],
                height=400,
                title=f"{taskname}",
                # toolbar_location=None,
                tools="xwheel_zoom,reset, box_zoom, xpan",
            )
            p.vbar(x="bitstrings", top="cnts", source=tsrc, width=0.9, color=color1)

            p.xgrid.grid_line_color = None
            p.xaxis.major_label_orientation = math.pi / 4
            p.y_range.start = 0
            p.yaxis.axis_label = "Counts"

            hov_tool = HoverTool()
            hov_tool.tooltips = [
                ("counts: ", "@cnts"),
                ("bitstrings:\n", "@bitstrings"),
            ]
            p.add_tools(hov_tool)

            pryd = figure(
                x_range=trydsrc.data["sites"],
                height=400,
                width=300,
                # toolbar_location=None,
                tools="xwheel_zoom,reset,box_zoom,xpan",
            )

            pryd.vbar(x="sites", top="ryds", source=trydsrc, width=0.5, color=color2)

            pryd.xgrid.grid_line_color = None
            pryd.y_range.start = 0
            pryd.yaxis.axis_label = "Rydberg density"
            pryd.xaxis.major_label_orientation = math.pi / 4
            pryd.xaxis.axis_label = "site"

            hov_tool = HoverTool()
            hov_tool.tooltips = [("density: ", "@ryds")]
            pryd.add_tools(hov_tool)

            pgeo = plot_register(geo)

            figs.append(row(div, p, pryd, pgeo, name=taskname))
            figs[-1].visible = False

        # Create a dropdown menu to select between the two graphs
        figs[0].visible = True
        multi_choice = MultiChoice(value=[options[0]], options=options)

        multi_choice.js_on_change(
            "value",
            CustomJS(
                args=dict(figs=figs, options=options, nelem=len(options)),
                code="""
                        const vals = this.value
                        for(let i=0;i<nelem;i++){
                            figs[i].visible=false;
                            for(let j=0;j<vals.length;j++){
                                if(vals[j]==options[i]){
                                    figs[i].visible=true;
                                    break;
                                }
                            }
                        }
                    """,
            ),
        )

    # headline = row(Div(text="Report: " + name), bt)
    headline = Div(text="Report: " + name)
    return column(headline, column(multi_choice, column(*figs)))


def bloqadeICON():
    with open("./logl.svg", "r") as f:
        lines = f.readlines()

    return lines


if __name__ == "__main__":
    dat = mock_data()

    fig = report_visual(*dat)

    show(fig)
    # from bokeh.models import SVGIcon

    # p = figure(width=200, height=100, toolbar_location=None)
    # p.image_url(url="file:///./logo.png")
    # button = Button(label="", icon=SVGIcon(svg=bloqadeICON(), size=50))
    # show(button)
