"""Section 2: the key figures at the top (they follow the filters) and the trend over time."""
import streamlit as st
 
import config as cfg
from utils.prep import summarize, weighted_share
from utils.viz import two_period_chart
 
# One entry per key figure. `years` = the years in which the question was asked.
KPIS = [
    {
        "flag": "sm_multi_daily",
        "label": "Use social networks several times a day",
        "years": (2023, 2024, 2025),
        "help": "Share of online respondents who consult a social network several times a day.",
    },
    {
        "flag": "screen_too_much",
        "label": "Feel they spend too much time on screens",
        "years": (2024,),
        "help": "Share answering 'too much' or 'far too much' time on their screens for personal use "
        "(all screens, not only social media).",
    },
    {
        "flag": "inappro5_often",
        "label": "Often or sometimes see self-harm content",
        "years": (2025,),
        "help": "Share who say they were often or sometimes exposed, without asking for it, to suicide or "
        "self-harm content on social networks.",
    },
]
 
 
def _years(spec):
    """The years in which the question was asked, written as text ("2024" or "2023-2025")."""
    years = spec["years"]
    return str(years[0]) if len(years) == 1 else f"{years[0]}-{years[-1]}"
 
 
def _pct(x):
    return f"{x * 100:.0f}%"
 
 
def render_kpis(data, baseline):
    """Row of key figures: the value for the selection, the value for everyone, and the margin of error."""
    is_baseline = len(data) == len(baseline)
    cols = st.columns(len(KPIS))
    for i, (col, spec) in enumerate(zip(cols, KPIS)):
        box = col.container(border=True, key=f"card_kpi{i}")
        s = summarize(data, spec["flag"])
        if s["n"] == 0:
            box.metric(spec["label"], "n/a", help=spec["help"])
            box.caption(f"Not asked in the selected years (asked in {_years(spec)}).")
            continue
        base = summarize(baseline, spec["flag"])
        delta = None if is_baseline else f"vs {_pct(base['share'])} for all respondents"        
        box.metric(spec["label"], _pct(s["share"]), delta, delta_color="off", delta_arrow="off", help=spec["help"])
        box.caption(f"{_years(spec)} · likely between {_pct(s['ci_low'])} and {_pct(s['ci_high'])} · {s['n']:,} respondents")
        
 
 
def _trend_headline(by_year):
    """One short sentence about the trend from 2023 to 2025, without claiming more than the data shows."""
    first, last = by_year.iloc[0], by_year.iloc[-1]
    text = f"In {int(last['year'])}, {last['share'] * 100:.0f}% check a social network several times a day"
    if len(by_year) == 1:
        return text + "."
    start = int(first["year"])
    if last["ci_low"] > first["ci_high"] or last["ci_high"] < first["ci_low"]:
        direction = "up" if last["share"] > first["share"] else "down"
        return text + f", {direction} from {first['share'] * 100:.0f}% in {start}."
    return text + f", about the same as in {start}."
 
 
def _participation_headline(by_year):
    """One short sentence for the 2009-2022 chart: how use changed between the first and the last year."""
    first, last = by_year.iloc[0], by_year.iloc[-1]
    if int(first["year"]) == int(last["year"]):
        return f"{last['share'] * 100:.0f}% used a social network in {int(last['year'])}."
    verb = "rose" if last["share"] >= first["share"] else "fell"
    return (f"Social network use {verb} from {first['share'] * 100:.0f}% in {int(first['year'])} "
            f"to {last['share'] * 100:.0f}% in {int(last['year'])}.")
 
 
 
 
def render_trends(data, baseline, adoption_sel, adoption_all):
    """Chart 1: use of social networks in 2009-2022, next to how often people check them in 2023-2025.
 
    The two periods ask different questions, so they are shown in two charts side by side
    instead of being joined in one line.
    """
    st.subheader(
        "Social networks over time",
        help="Two different survey questions, so we have two different panels to show the evolution. The highlighted part around each "
        "line is the 95% margin of error. From 2020 the survey is mostly online, which may explain part of the "
        "change around that year.",
    )
    long_sel = weighted_share(adoption_sel, "participates", "year")
    recent_sel = weighted_share(data, "sm_multi_daily", "year")
    if long_sel.empty:
        st.info("No respondent matches the age and sex filters for 2009-2022.")
        return
    # Each sentence sits above its own chart (same 60 / 40 split as the figure).
    left, right = st.columns([0.6, 0.4])
    left.markdown(_participation_headline(long_sel))
    if not recent_sel.empty:
        right.markdown(_trend_headline(recent_sel))
    else:
        right.info("Select at least one survey year (2023-2025) to see the recent figures.")
 
    # The comparison line only appears when the selection is different from everyone.
    long_all = None if len(adoption_sel) == len(adoption_all) else weighted_share(adoption_all, "participates", "year")
    recent_all = None if len(data) == len(baseline) else weighted_share(baseline, "sm_multi_daily", "year")
    st.plotly_chart(
        two_period_chart(
            long_sel, long_all, recent_sel, recent_all,
                        titles=("Use a social network at all<br>2009-2022",
                    "Check social network several times a day<br>2023-2025"),
            break_year=cfg.ADOPTION_BREAK_YEAR, break_label="Survey went online (2020)",
            ),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.caption(
        "Chart description: two line charts with 95% confidence bands, by survey year. On the left, we have the share of people who "
        "use a social network (2009-2022). On the right, we have the share of people who check a social network several times a day (2023-2025). "
        "A dotted line shows all respondents when the selection differs."
    )
 
 
def render(data, baseline, adoption_sel, adoption_all):
    st.header("Overview")
    render_kpis(data, baseline)
    with st.container(border=True, key="card_trend"):
        render_trends(data, baseline, adoption_sel, adoption_all)
 