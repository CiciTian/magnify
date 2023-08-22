from typing import Callable
import functools
import itertools
import math

from plotly.subplots import make_subplots
import panel as pn
import plotly
import plotly.graph_objects as go
import xarray as xr

import magnify.utils as utils


def ndplot(
    xp,
    plot_function,
    facet_row: str | None = None,
    facet_col: str | None = None,
    facet_col_wrap: int = 0,
    animation_frame: str | None = None,
    **kwargs,
):
    def get_facet(idx=None):
        if animation_frame is not None:
            if idx is None:
                sub_xp = xp.isel({animation_frame: 0})
            else:
                sub_xp = xp.sel({animation_frame: idx})
        else:
            sub_xp = xp

        indexes = []
        if facet_row is not None and facet_col is not None:
            fig = make_subplots(rows=len(sub_xp[facet_row]), cols=len(sub_xp[facet_col]))
            for i in range(len(sub_xp[facet_row])):
                for j in range(len(sub_xp[facet_col])):
                    traces = plot_function(sub_xp.isel({facet_row: i, facet_col: j}), **kwargs)
                    for trace in traces:
                        fig.add_trace(
                            trace,
                            row=i + 1,
                            col=j + 1,
                        )
        elif facet_col is not None:
            if facet_col_wrap == 0:
                num_cols = len(sub_xp[facet_col])
            else:
                num_cols = facet_col_wrap
            num_rows = math.ceil(len(sub_xp[facet_col]) / num_cols)
            fig = make_subplots(rows=num_rows, cols=num_cols)
            for i in range(len(sub_xp[facet_col])):
                traces = plot_function(sub_xp.isel({facet_col: i}), **kwargs)
                for trace in traces:
                    fig.add_trace(trace, row=i // num_cols + 1, col=i % num_cols + 1)
        elif facet_row is not None:
            fig = make_subplots(rows=len(sub_xp[facet_row]), cols=1)
            for i in range(len(sub_xp[facet_row])):
                traces = plot_function(sub_xp.isel({facet_row: i}), **kwargs)
                for trace in traces:
                    fig.add_trace(trace, row=i + 1, col=1)
        else:
            fig = go.Figure(data=plot_function(sub_xp, **kwargs))

        return fig

    fig = get_facet()
    if animation_frame is not None:
        fig.frames = [
            go.Frame(name=str(idx), data=get_facet(idx).data[0], traces=[0])
            for idx in xp[animation_frame].values
        ]
        fig.layout.sliders = [
            go.layout.Slider(
                active=0,
                steps=[
                    {
                        "args": [
                            [f.name],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                                "fromcurrent": True,
                                "transition": {"duration": 300, "easing": "linear"},
                            },
                        ],
                        "label": f.name,
                        "method": "animate",
                    }
                    for k, f in enumerate(fig.frames)
                ],
            )
        ]

    return fig
