"""Section 5: what we found, what it means, and what to do next.
 
All the figures are calculated from the data. A difference is only presented as a finding
when the data supports it (the margins of error do not overlap).
"""
import streamlit as st
 
import config as cfg
from utils.prep import weighted_share
 
 
def _pct(x):
    return f"{x * 100:.0f}%"
 
 
def _row(frame, flag):
    return weighted_share(frame, flag).iloc[0]
 
 
def _differs(a, b):
    """True when the margins of error of the two shares do not overlap, so the difference is real."""
    return a["ci_low"] > b["ci_high"] or a["ci_high"] < b["ci_low"]
 
 
def _big(number):
    """The big number at the top of a card, in the accent colour."""
    st.markdown(
        f'<div style="font-family: Newsreader, Georgia, serif; font-size: 3.4rem; font-weight: 600; '
        f'line-height: 1.1; color: light-dark(#0b6180, #6fcfe3)">{number}</div>',
        unsafe_allow_html=True,
    )
 
 
def _use_insight(analysis):
    everyone = _row(analysis, "sm_multi_daily")
    by_year = weighted_share(analysis, "sm_multi_daily", "year")
    first, last = by_year.iloc[0], by_year.iloc[-1]
    if _differs(first, last):
        trend = f"that has gone {'up' if last['share'] > first['share'] else 'down'} since {int(first['year'])}"
    else:
        trend = f"that has not clearly changed since {int(first['year'])}"
    youth = _row(analysis[analysis["youth"]], "sm_multi_daily")
    adults = _row(analysis[analysis["age_group"] == "25-39"], "sm_multi_daily")
    seniors = _row(analysis[analysis["age_group"].isin(["60-69", "70+"])], "sm_multi_daily")
    if not _differs(youth, adults):
        compare = (f"The heaviest users are not the youngest: 12-24 year-olds ({_pct(youth['share'])}) are about "
                   f"level with 25-39 year-olds ({_pct(adults['share'])})")
    elif youth["share"] > adults["share"]:
        compare = (f"Young people lead: 12-24 year-olds ({_pct(youth['share'])}) are above 25-39 year-olds "
                   f"({_pct(adults['share'])})")
    else:
        compare = (f"The heaviest users are not the youngest: 12-24 year-olds ({_pct(youth['share'])}) are below "
                   f"25-39 year-olds ({_pct(adults['share'])})")
    return _pct(everyone["share"]), (
        f"of people online check a social network several times a day, and {trend}. {compare}, while people aged "
        f"60 and over are at {_pct(seniors['share'])}."
    )
 
 
def _screen_insight(analysis):
    asked = analysis[(analysis["year"] == 2024) & analysis["freq_group"].notna()]
    by_use = weighted_share(asked, "screen_too_much", "freq_group").set_index("freq_group")
    heavy, light = by_use.loc["Several times a day"], by_use.loc["Less often or never"]
    return _pct(heavy["share"]), (
        "of those who check a social network several times a day feel they spend too much time on screens, "
        f"against {_pct(light['share'])} of those who use them less often or never (2024). The two go together, "
        "but that doesn't prove social networks cause the feeling."
    )
 
 
def _exposure_gaps(analysis):
    """The types of content that young people see more than everyone else (2025), biggest difference first."""
    year = analysis[analysis["year"] == 2025]
    youth = year[year["youth"]]
    gaps = []
    for k, label in cfg.INAPPRO_ITEMS.items():
        flag = f"inappro{k}_often"
        everyone, young = _row(year, flag), _row(youth, flag)
        if young["ci_low"] > everyone["share"]:
            gaps.append(((young["share"] - everyone["share"]) * 100, label.lower(), young["share"], everyone["share"]))
    gaps.sort(reverse=True)
    return gaps
 
 
def _exposure_insight(analysis):
    gaps = _exposure_gaps(analysis)
    if not gaps:
        return "-", ("In 2025, young people do not report being exposed to any type of content more than all "
                     "respondents, beyond the margin of error.")
    _, label, young, everyone = gaps[0]
    total = len(cfg.INAPPRO_ITEMS)
    text = (f"of young people often or sometimes come across {label} without looking for it, against "
            f"{_pct(everyone)} of everyone (2025). They see more of "
            + ("every one of the " if len(gaps) == total else f"{len(gaps)} of the ")
            + f"{total} types we asked about")
    if len(gaps) >= 2:
        text += f", and {gaps[1][1]} comes next ({_pct(gaps[1][2])} vs {_pct(gaps[1][3])})"
    return _pct(young), text + "."
 
 
def _region_sentence(analysis):
    overall = _row(analysis, "sm_multi_daily")
    table = weighted_share(analysis, "sm_multi_daily", "region")
    table = table[table["n_eff"] >= cfg.MIN_N_EFF]
    far = int(((table["ci_low"] > overall["share"]) | (table["ci_high"] < overall["share"])).sum())
    if far <= len(table) / 4:
        return (f"Regions hardly differ (only {far} of {len(table)} are far from the national figure), so this "
                "survey alone doesn't justify targeting by region.")
    return (f"Several regions differ from the national figure ({far} of {len(table)}), so a regional angle may be "
            "worth exploring.")
 
 
def render(analysis):
    st.header("Key insights and next steps")
 
    st.subheader("What we found")
    insights = [_use_insight, _screen_insight, _exposure_insight]
    for i, (col, insight) in enumerate(zip(st.columns(3), insights)):
        number, text = insight(analysis)
        with col.container(border=True, key=f"card_insight{i}"):
            _big(number)
            st.markdown(text)
 
    st.subheader("What it means")
    gaps = _exposure_gaps(analysis)
    tools = ("reporting and moderation tools matter most for the content types where young people see the most"
             + (f", like {gaps[0][1]} and {gaps[1][1]}" if len(gaps) >= 2 else ""))
    st.markdown(
        "- **For educators and parents:** the question may be less how many hours young people spend online than "
        "what they come across there. They are not the heaviest users, but they do report more unwanted content.\n"
        f"- **For decision-makers:** {tools}. {_region_sentence(analysis)}"
    )
 
    st.subheader("Limits and next steps")
    st.markdown(
        "- People tell us what they feel and remember, so these figures are opinions and not measurements.\n"
        "- Each year interviews different people, so we can compare groups but never follow the same person over "
        "time.\n"
        "- Ages are only split into six groups, which hides differences inside each group.\n"
        "- Next, we would add the coming survey years to see whether the picture holds.\n"
        "- We would also look for a source that follows the same people over time.\n"
        "- Finally, we would ask about time spent on social networks rather than on all screens."
    )
 