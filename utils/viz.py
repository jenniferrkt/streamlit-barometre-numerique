"""All the charts of the app, so that they share the same look.
 
Colours: blue = the current selection, coral = all respondents (the comparison).
They were chosen to stay readable in light and dark mode.
"""
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
 
# The same group always has the same colour, in every chart.
SERIES_COLORS = {
    "light": {"selection": "#0b6180", "everyone": "#f25a5a"},
    "dark": {"selection": "#6fcfe3", "everyone": "#ee7b75"},
}
# Neutral colours for the text, the grid lines and the ring around each dot.
CHROME = {
    "light": {"text": "#0e2a35", "muted": "#4a5d66", "grid": "#e2ecef", "surface": "#ffffff"},
    "dark": {"text": "#eef6f8", "muted": "#b8ccd3", "grid": "#25536a", "surface": "#173a49"},
}
 
 
def _theme():
    """Say whether the page is in 'light' or 'dark' mode, so the charts can use matching colours."""
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"
 
 
def _hex_to_rgba(color, alpha):
    r, g, b = (int(color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"
 
 
def _add_series(fig, col, table, name, color, ring, show_legend, dash="solid"):
    """Draw one line and the band of its margin of error, in panel `col` of the figure."""
    if table is None or table.empty:
        return
    x = table["year"].tolist()
    low = (table["ci_low"] * 100).tolist()
    high = (table["ci_high"] * 100).tolist()
    if len(x) > 1:  # confidence band: a pale wash of the series colour between low and high
        fig.add_trace(go.Scatter(
            x=x + x[::-1], y=high + low[::-1], fill="toself", mode="lines",
            fillcolor=_hex_to_rgba(color, 0.12), line=dict(width=0),
            hoverinfo="skip", showlegend=False, legendgroup=name,
        ), row=1, col=col)
    fig.add_trace(go.Scatter(
        x=x, y=(table["share"] * 100).tolist(), name=name, mode="lines+markers",
        line=dict(color=color, width=2, dash=dash),
        marker=dict(size=9, color=color, line=dict(color=ring, width=2)),
        customdata=list(zip(low, high, table["n"], table["n_eff"].round(0))),
        hovertemplate=(
            "<b>%{x}</b> - " + name + "<br>"
            "%{y:.0f}% <br>likely between %{customdata[0]:.0f}% and %{customdata[1]:.0f}%<br>"
            "%{customdata[2]:,} respondents"
            "<extra></extra>"
        ),
        showlegend=show_legend, legendgroup=name,
    ), row=1, col=col)
 
 
def two_period_chart(long_sel, long_all, recent_sel, recent_all, titles, break_year=None, break_label=""):
    """One figure with two charts side by side, sharing the same vertical axis (0 to 100%).
 
    The two periods answer different questions, so they are NOT joined in one line:
    the left chart covers 2009-2022 and the right chart covers 2023-2025.
 
    Each table has the columns year, share, ci_low, ci_high, n and n_eff (see weighted_share in
    utils/prep.py). `*_all` is the comparison group: pass None to leave it out.
    `titles` = (title of the left chart, title of the right chart).
    `break_year` = the first year of the left chart when the survey changed its method.
    That part is shaded and labelled with `break_label`.
    """
    theme = _theme()
    colors, chrome = SERIES_COLORS[theme], CHROME[theme]
    fig = make_subplots(
        rows=1, cols=2, shared_yaxes=True, column_widths=[0.6, 0.4],
        horizontal_spacing=0.07, subplot_titles=titles,
    )
    fig.update_annotations(font=dict(color=chrome["text"], size=13))  # panel titles
 
    for col, selected, everyone in ((1, long_sel, long_all), (2, recent_sel, recent_all)):
        _add_series(fig, col, selected, "Selection", colors["selection"], chrome["surface"], col == 1)
        _add_series(fig, col, everyone, "All respondents", colors["everyone"], chrome["surface"], col == 1, dash="dot")
 
    if break_year is not None and not long_sel.empty:
        fig.add_vrect(
            x0=break_year - 0.5, x1=long_sel["year"].max() + 0.5,
            fillcolor=_hex_to_rgba(chrome["muted"], 0.10), line_width=0, layer="below",
            annotation_text=break_label, annotation_position="bottom left",
            annotation_font=dict(color=chrome["muted"], size=12), row=1, col=1,
        )
 
    axis = dict(showgrid=False, linecolor=chrome["grid"], zeroline=False, tickangle=0, title="Survey year")
    fig.update_xaxes(tickmode="array", tickvals=sorted(long_sel["year"].unique()), range=[2008.4, 2022.6], **axis, col=1)
    fig.update_xaxes(tickmode="array", tickvals=[2023, 2024, 2025], range=[2022.5, 2025.5], **axis, col=2)
    fig.update_yaxes(
        range=[0, 100], ticksuffix="%", gridcolor=chrome["grid"], gridwidth=1, zeroline=False,
    )
    fig.update_yaxes(title="Share of respondents (%)", col=1)
    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=90, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=chrome["muted"], size=13),
        hovermode="x unified",
        legend=dict(orientation="h", y=1.3, x=0, font=dict(color=chrome["text"])),
    )
    return fig
 
 
# A lighter shade of the selection colour, for the bars that are not selected.
OTHER_BARS = {"light": "#9ad7e8", "dark": "#1d5f78"}
 
 
def _text_on(color):
    """Choose dark or white text, whichever is easier to read on a bar of this colour."""
    r, g, b = (int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return "#0e2a35" if 0.2126 * r + 0.7152 * g + 0.0722 * b > 0.35 else "#ffffff"
 
 
def _error_bar(chrome, share, low, high, horizontal=False):
    """The small whiskers that show the margin of error, in the same colour as the text."""
    return dict(type="data", symmetric=False, array=(high - share).tolist(), arrayminus=(share - low).tolist(),
                color=chrome["text"], thickness=2, width=7)
 
 
def bar_chart(series, x, x_title, y_title="Share of respondents (%)", grouped=False):
    """Vertical bars with the value written at the bottom of each bar and a whisker for the margin of error.
 
    `series` is a list of (name, colour, table). The colour is "selection", "everyone" or "other".
    Each table has the column `x` (the category), plus share, ci_low, ci_high, n and n_eff.
    With `grouped=True`, the series sit side by side for each category. Otherwise they are drawn
    on top of each other (used when each category belongs to only one series).
    A series with an empty table is skipped, and a series named "" is left out of the legend.
    """
    theme = _theme()
    chrome = CHROME[theme]
    colors = {**SERIES_COLORS[theme], "other": OTHER_BARS[theme]}
    series = [(name, key, table) for name, key, table in series if table is not None and not table.empty]
    categories = list(dict.fromkeys(c for _, _, table in series for c in table[x].astype(str)))
    fig = go.Figure()
    for name, key, table in series:
        share, low, high = table["share"] * 100, table["ci_low"] * 100, table["ci_high"] * 100
        fig.add_trace(go.Bar(
            x=table[x].astype(str), y=share, name=name, showlegend=bool(name),
            marker=dict(color=colors[key], cornerradius=4),
            error_y=_error_bar(chrome, share, low, high),
            text=[f"{v:.0f}%" for v in share], textposition="inside", insidetextanchor="start",
            textfont=dict(color=_text_on(colors[key]), size=13),
            customdata=list(zip(low, high, table["n"], table["n_eff"].round(0))),
            hovertemplate=(
                "<b>%{x}</b> - " + name + "<br>%{y:.0f}% <br>likely between %{customdata[0]:.0f}% and %{customdata[1]:.0f}%<br>"
                "%{customdata[2]:,} respondents<extra></extra>"
            ),
        ))
    top = max(float(table["ci_high"].max()) for _, _, table in series) * 100
    fig.update_layout(
        height=380, barmode="group" if grouped else "overlay", bargap=0.35, bargroupgap=0.1,
        hovermode="closest", margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=chrome["muted"], size=13),
        legend=dict(orientation="h", y=1.08, x=0, font=dict(color=chrome["text"])),
        xaxis=dict(title=x_title, showgrid=False, linecolor=chrome["grid"], zeroline=False,
                   categoryorder="array", categoryarray=categories),
        yaxis=dict(title=y_title, range=[0, min(100, top * 1.15)], ticksuffix="%",
                   gridcolor=chrome["grid"], gridwidth=1, zeroline=False),
    )
    return fig
 
 
def bar_dot_chart(sel, everyone, y, value_title):
    """Horizontal bars for the selection, with one diamond per category for all respondents.
 
    This is easier to read than two thin bars per row when there are many categories.
    Both tables have the columns `y` (the category), share, ci_low, ci_high, n and n_eff,
    sorted in the order they should appear (first row on top). With `everyone=None`, the diamonds are left out.
    """
    theme = _theme()
    chrome, colors = CHROME[theme], SERIES_COLORS[theme]
    categories = sel[y].astype(str).tolist()
    share, low, high = sel["share"] * 100, sel["ci_low"] * 100, sel["ci_high"] * 100
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=categories, x=share, orientation="h", name="Selection",
        marker=dict(color=colors["selection"], cornerradius=4),
        error_x=_error_bar(chrome, share, low, high),
        customdata=list(zip(low, high, sel["n"], sel["n_eff"].round(0))),
        hovertemplate=("<b>%{y}</b> - Selection<br>%{x:.0f}% <br>likely between %{customdata[0]:.0f}% and %{customdata[1]:.0f}%<br>"
                       "%{customdata[2]:,} respondents<extra></extra>"),
    ))
    # The value is written just after the whiskers, using a separate text-only trace.
    fig.add_trace(go.Scatter(
        y=categories, x=(high + 2.5).tolist(), mode="text", text=[f"{v:.0f}%" for v in share], textposition="middle right",
        textfont=dict(color=chrome["text"], size=13), hoverinfo="skip", showlegend=False,
    ))
    if everyone is not None and not everyone.empty:
        every = everyone.set_index(everyone[y].astype(str)).loc[categories]
        fig.add_trace(go.Scatter(
            y=categories, x=(every["share"] * 100).tolist(), mode="markers", name="All respondents",
            marker=dict(symbol="diamond", size=13, color=colors["everyone"], line=dict(color=chrome["surface"], width=2)),
            customdata=list(zip(every["ci_low"] * 100, every["ci_high"] * 100, every["n"], every["n_eff"].round(0))),
            hovertemplate=("<b>%{y}</b> - All respondents<br>%{x:.0f}% <br>likely between %{customdata[0]:.0f}% and %{customdata[1]:.0f}%<br>"
                           "%{customdata[2]:,} respondents<extra></extra>"),
        ))
    top = float(high.max())
    fig.update_layout(
        height=430, bargap=0.45, hovermode="closest", margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=chrome["muted"], size=13),
        legend=dict(orientation="h", y=1.07, x=0, font=dict(color=chrome["text"])),
        yaxis=dict(title="", autorange="reversed", categoryorder="array", categoryarray=categories,
                   showgrid=False, linecolor=chrome["grid"]),
        xaxis=dict(title=value_title, range=[0, min(100, top * 1.18)], ticksuffix="%",
                   gridcolor=chrome["grid"], gridwidth=1, zeroline=False),
    )
    return fig
 
 
# Map colours: one colour that goes from light (low) to dark (high), and grey for regions with too few respondents.
MAP_RAMP = {
    "light": ["#bfe6f0", "#5fb8d4", "#0b6180", "#073d52"],
    "dark": ["#0b5f78", "#0891b2", "#5fd0ea", "#d3f3fb"],
}
MAP_STYLE = {"light": "carto-positron", "dark": "carto-darkmatter"}
NO_DATA_GREY = "#898781"
 
 
def region_map_chart(table, min_n_eff, value_title):
    """Map of mainland France with one circle per region, coloured by the share.
 
    `table` has the columns region, lat, lon, share, ci_low, ci_high, n and n_eff.
    Regions whose effective sample size is below `min_n_eff` are drawn in grey,
    because their percentage is not reliable.
    """
    theme = _theme()
    chrome = CHROME[theme]
    ok = table[table["n_eff"] >= min_n_eff]
    few = table[table["n_eff"] < min_n_eff]
    fig = go.Figure()
 
    def hover(part):
        return list(zip(part["region"], part["share"] * 100, part["ci_low"] * 100, part["ci_high"] * 100,
                        part["n"], part["n_eff"].round(0)))
 
    if not few.empty:
        fig.add_trace(go.Scattermap(
            lat=few["lat"], lon=few["lon"], mode="markers", name=f"Too few respondents (< {min_n_eff})",
            marker=dict(size=26, color=NO_DATA_GREY, opacity=0.9),
            customdata=hover(few),
            hovertemplate=("<b>%{customdata[0]}</b><br>Too few respondents for a reliable figure<br>"
                           "%{customdata[4]:,} respondents<extra></extra>"),
        ))
    if not ok.empty:
        ramp = MAP_RAMP[theme]
        fig.add_trace(go.Scattermap(
            lat=ok["lat"], lon=ok["lon"], mode="markers+text", name="Region",
            text=[f"{v:.0f}%" for v in ok["share"] * 100], textposition="top center",
            textfont=dict(color=chrome["text"], size=12),
            marker=dict(
                size=26, opacity=0.95, color=(ok["share"] * 100).tolist(),
                colorscale=[[i / (len(ramp) - 1), c] for i, c in enumerate(ramp)],
                colorbar=dict(title=dict(text=value_title, font=dict(color=chrome["muted"])),
                              ticksuffix="%", tickfont=dict(color=chrome["muted"]), len=0.6, thickness=12),
            ),
            customdata=hover(ok),
            hovertemplate=("<b>%{customdata[0]}</b><br>%{customdata[1]:.0f}% "
                           "<br>likely between %{customdata[2]:.0f}% and %{customdata[3]:.0f}%<br>"
                           "%{customdata[4]:,} respondents<extra></extra>"),
            showlegend=False,
        ))
    fig.update_layout(
        height=560, margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        map=dict(style=MAP_STYLE[theme], center=dict(lat=46.6, lon=2.6), zoom=4.7),
        legend=dict(orientation="h", y=0.02, x=0.01, font=dict(color=chrome["text"]),
                    bgcolor="rgba(0,0,0,0)"),
    )
    return fig
 