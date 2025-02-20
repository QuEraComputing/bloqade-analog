from bloqade.analog.visualization.report_visualize import mock_data, report_visual


def test_report_vis_mock():
    dat = mock_data()

    report_visual(*dat)

    # from bokeh.models import SVGIcon

    # p = figure(width=200, height=100, toolbar_location=None)
    # p.image_url(url="file:///./logo.png")
    # button = Button(label="", icon=SVGIcon(svg=bloqadeICON(), size=50))
    # show(button)
