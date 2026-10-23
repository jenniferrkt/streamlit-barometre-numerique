"""Section 3: the four detailed charts (by age, by region, screen time and unwanted content)."""
import re
 
import pandas as pd
import streamlit as st
 
import config as cfg
from utils.prep import weighted_share
from utils.viz import bar_chart, bar_dot_chart, region_map_chart
 
 
def _emph(text):
    """Put only the percentages in bold, inside a sentence."""
    return re.sub(r"([+-]?\d+(?:%))", r"**\1**", text)
 
 
def _age_headline(table, years):
    """One sentence: where the share is highest and lowest, and which groups are about as high as the top."""
    top = table.loc[table["share"].idxmax()]
    bottom = table.loc[table["share"].idxmin()]
    text = (f"It peaks at {top['share'] * 100:.0f}% among {top['age_group']} and falls to "
            f"{bottom['share'] * 100:.0f}% among {bottom['age_group']} ({years}).")
    # If a group's margin of error overlaps the top group's, we cannot tell them apart.
    close = [str(r["age_group"]) for _, r in table.iterrows()
             if r["age_group"] != top["age_group"] and r["ci_high"] >= top["ci_low"]]
    if len(close) == 1:
        text += f" The {close[0]} group is about as high as the peak."
    elif close:
        text += f" The {' and '.join(close)} groups are about as high as the peak."
    return text
 
 
def _region_headline(table, years):
    """One sentence: the regions with the lowest and highest share, and whether the gap is bigger than the margin of error."""
    reliable = table[table["n_eff"] >= cfg.MIN_N_EFF]
    if reliable.empty:
        return "No region has enough respondents for a reliable figure."
    top = reliable.loc[reliable["share"].idxmax()]
    bottom = reliable.loc[reliable["share"].idxmin()]
    text = (f"Depending on the region, between {bottom['share'] * 100:.0f}% ({bottom['region']}) and "
            f"{top['share'] * 100:.0f}% ({top['region']}), all ages ({years}). ")
    if top["ci_low"] <= bottom["ci_high"]:
        return text + "Once the margin of error is counted, the regions cannot really be told apart."
    return text + "That gap is real as it is larger than the survey's margin of error."
 
 
def _years_text(frame, column):
    """The years in which the question was asked, and the same years written as text ("2024" or "2023-2025")."""
    asked = sorted(frame.loc[frame[column].notna(), "year"].unique())
    if not asked:
        return asked, ""
    if len(asked) == 1:
        return asked, str(asked[0])
    return asked, f"{asked[0]}-{asked[-1]}"
 
 
def render(by_age, ages, indicator, by_region, data, baseline):
    """What each input contains:
    `by_age`: the chosen years, sex and regions, with all age groups kept.
    `by_region`: the chosen years and sex, with all ages and all regions kept (used by the map).
    `data` and `baseline`: the selection, and everyone, for the screen time chart."""
    st.header("Deep dives")
    left, right = st.columns(2)
    with left.container(border=True, key="card_age"):
        render_age(by_age, ages, indicator)
    with right.container(border=True, key="card_map"):
        render_map(by_region, indicator)
    left, right = st.columns(2)
    with left.container(border=True, key="card_screen"):
        render_screen_time(data, baseline)
    with right.container(border=True, key="card_exposure"):
        render_exposure(data, baseline)
 
 
def _freq_table(frame):
    return weighted_share(frame[frame["year"] == 2024], "screen_too_much", "freq_group")
 
 
def render_screen_time(data, baseline):
    st.subheader(
        "Do heavy users feel they spend too much time on their screens?",
        help="Screen time covers all screens, not only social networks. The chart shows an association, "
        "not a cause.",
    )
    sel = _freq_table(data[data["freq_group"].notna()])
    if sel.empty:
        st.info("This question was asked in 2024 only. Include 2024 in the survey years and keep respondents who use the internet.")
        return
    everyone = None if len(data) == len(baseline) else _freq_table(baseline[baseline["freq_group"].notna()])
    top = sel[sel["freq_group"] == "Several times a day"]
    low = sel[sel["freq_group"] == "Less often or never"]
    if not top.empty and not low.empty:
        t, l = top.iloc[0], low.iloc[0]
        text = (f"Heavy users feel it more: {t['share'] * 100:.0f}% of those who check a social network several "
                f"times a day say they spend too much time on screens, against {l['share'] * 100:.0f}% of those who "
                "use them less often or never (2024).")
        if l["n_eff"] < cfg.MIN_N_EFF:
            text += f" Only a small group uses them less often or never, so treat the {l['share'] * 100:.0f}% with care."
        st.markdown(_emph(text))
    st.plotly_chart(
        bar_chart(
            [("Selection", "selection", sel), ("All respondents", "everyone", everyone)],
            x="freq_group", x_title="How often the person checks a social network",
            y_title="Feel they spend too much time on screens (%)", grouped=True,
        ),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.caption(
        "Chart description: bars with 95% error bars. For three levels of social network use (less often or "
        "never, daily or almost daily, several times a day), the share who feel they spend too much time on "
        "screens, for the selection and for all respondents (2024)."
    )
 
 
def render_age(by_age, ages, indicator):
    st.subheader("Does age make a difference?")
    column = cfg.INDICATORS[indicator]
    asked, years = _years_text(by_age, column)
    if not asked:
        st.info(f"'{indicator}' was not asked in the selected survey years. Widen the year range in the sidebar.")
        return
    table = weighted_share(by_age, column, "age_group")
    st.markdown(_emph(f"{indicator}: {_age_headline(table, years)}"))
    st.plotly_chart(
        bar_chart(
            [("Selected age group(s)", "selection", table[table["age_group"].isin(ages)]),
             ("Other age groups", "other", table[~table["age_group"].isin(ages)])],
            x="age_group", x_title="Age group",
        ),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.caption(
        "Chart description: one bar per age group (12-17 to 70+) with 95% error bars, showing the share for the "
        "chosen measure. The selected age groups are highlighted."
    )
 
 
def render_map(by_region, indicator):
    st.subheader("Does where you live matter?")
    column = cfg.INDICATORS[indicator]
    asked, years = _years_text(by_region, column)
    if not asked:
        st.info(f"'{indicator}' was not asked in the selected survey years. Widen the year range in the sidebar.")
        return
    table = weighted_share(by_region, column, "region")
    table["lat"] = table["region"].map(lambda r: cfg.REGION_COORDS[r][0])
    table["lon"] = table["region"].map(lambda r: cfg.REGION_COORDS[r][1])
    st.markdown(_emph(f"{indicator}: {_region_headline(table, years)}"))
    st.plotly_chart(
        region_map_chart(table, cfg.MIN_N_EFF, "% of respondents"),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.caption(
        "Chart description: map of the French regions, all ages. The darker the circle, the higher the share for "
        "the chosen measure. A grey circles mark regions with too few respondents. Hover a region for its value."
    )
 
 
def _exposure_table(frame):
    """For each type of unwanted content, the share of people who see it often or sometimes (2025 only)."""
    rows = []
    for k, label in cfg.INAPPRO_ITEMS.items():
        result = weighted_share(frame[frame["year"] == 2025], f"inappro{k}_often")
        if not result.empty and result.iloc[0]["n"] > 0:
            rows.append({**result.iloc[0].to_dict(), "content": label})
    return pd.DataFrame(rows)
 
 
def render_exposure(data, baseline):
    st.subheader(
        "What do people come across without looking for it?",
        help="Often or sometimes exposed, without looking for it, on social networks. It does not measure the "
        "effect on wellbeing, and people who are online more often naturally see more.",
    )
    sel = _exposure_table(data)
    if sel.empty:
        st.info("This question was asked in 2025 only. Include 2025 in the survey years.")
        return
    sel = sel.sort_values("share", ascending=False)
    everyone = None if len(data) == len(baseline) else _exposure_table(baseline)
    top = sel.iloc[0]
    text = f"{top['content']} is what people come across most ({top['share'] * 100:.0f}%, 2025)."
    if everyone is not None:
        gap = sel.merge(everyone, on="content", suffixes=("", "_all"))
        gap["diff"] = (gap["share"] - gap["share_all"]) * 100
        gap["clear"] = (gap["ci_low"] > gap["ci_high_all"]) | (gap["ci_high"] < gap["ci_low_all"])
        clear = gap[gap["clear"]]
        if clear.empty:
            text += " Nothing stands out compared with all respondents."
        else:
            best = clear.loc[clear["diff"].abs().idxmax()]
            text += (f" The biggest difference with everyone else: {best['content'].lower()}, seen by "
                     f"{best['share'] * 100:.0f}% of the selection against {best['share_all'] * 100:.0f}% of all respondents.")
    st.markdown(_emph(text))
    st.plotly_chart(
        bar_dot_chart(sel, everyone, y="content",
                      value_title="Often or sometimes exposed, without looking for it (%)"),
        width="stretch",
        config={"displayModeBar": False},
    )
    st.caption(
        "Chart description: horizontal bars with 95% error bars, one per type of unwanted content (2025), for "
        "the selection. A diamond marks the share for all respondents."
    )
 