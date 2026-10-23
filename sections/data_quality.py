"""Section 4: how far we can trust the data (checks, missing answers and things to keep in mind)."""
import streamlit as st
 
import config as cfg
 
 
def render(all_data, tables, report):
    raw, ext = report["raw"], report["extract"]
    asked = tables["asked"]
    nonresp = tables["nonresponse"]
 
    st.header("How far can we trust these numbers?")
    dont_know = nonresp.loc["Weekly screen hours", 2024]
    asked_sm = asked.loc["Social network use frequency", 2025]
    st.markdown(
        f"Most of the gaps you may notice are not errors: the survey does not ask the same questions every year, "
        f"and only people who go online were asked about social networks ({asked_sm:.0f}% of respondents). "
        f"The real weak spot is screen time: in 2024, **{dont_know:.0f}%** answered \"I don't know\" about their "
        f"weekly hours, so we only use it as context."
    )
 
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Answers in the survey", f"{raw['rows']:,}", f"{raw['columns']:,} questions in total, across all years",
              delta_color="off", delta_arrow="off")
    c2.metric("Answers used here", f"{ext['rows']:,}", f"years {ext['years'][0]}-{ext['years'][-1]}",
              delta_color="off", delta_arrow="off")
    c3.metric("Survey years", f"{len(raw['years'])}", f"no survey in {raw['years_without_wave'][0]}",
              delta_color="off", delta_arrow="off")
    c4.metric("Duplicated respondents", f"{raw['duplicate_ident']}", "none found" if raw["duplicate_ident"] == 0 else None,
              delta_color="off", delta_arrow="off")
 
    with st.expander("For the curious: checks and method notes"):
        checks = tables["checks"]
        failed = int((checks["Result"] != "Passed").sum())
        st.subheader("Checks we ran")
        st.markdown(
            f"Before using the data, we ran {len(checks)} checks: no duplicated respondents, every respondent has a "
            f"survey weight, the right years are present, and so on. "
            + ("All of them passed. " if failed == 0 else f"{failed} failed, see below. ")
            + "The survey weight is the coefficient that makes the sample match the French population: each "
            "respondent counts for more or less depending on how well their group is represented in the sample."
        )
        st.dataframe(checks, hide_index=True, width="stretch")
 
        st.subheader("Missing answers")
        st.markdown(
            "A blank does not always mean a missing answer: sometimes the question was simply not asked that year "
            "(shown as \"not asked\"). Among the people who were asked, some answered \"I don't know\" or gave no "
            "answer: the second tab shows how many."
        )
        t1, t2 = st.tabs(["Who was asked each question?", "Who did not answer?"])
        with t1:
            st.dataframe(asked.style.format(lambda v: "not asked" if v == 0 else f"{v:.0f}%"), width="stretch")
        with t2:
            st.dataframe(nonresp.style.format(lambda v: f"{v:.1f}%", na_rep="not asked"), width="stretch")
 
        corse = all_data[(all_data["region"] == "Corse") & all_data["social_freq"].notna()]
        youth = all_data[all_data["age_group"] == "12-17"]
        st.subheader("What to keep in mind")
        st.markdown(
            f"""
- **Some groups are small:** only about {len(youth) // len(cfg.YEARS)} respondents per year are aged 12-17, and Corse has just {len(corse)} answers about social networks over the three years. Before reading anything into a gap, look at the margin of error.
- **Two periods, two questions:** before 2023, the survey asked only whether people used a social network at all. From 2023, it asks how often. The two can't be joined in one curve. There is also no survey in 2021, and from 2020 the sample is twice as large and almost entirely online, so part of the change around 2020 may come from the method.
- **Different people each year:** each year interviews new people, so we compare groups and years, never the same individuals over time.
- **Opinions, not measures:** "too much" screen time is a feeling, and it covers all screens. Unwanted content is what people remember coming across.
- **The map is approximate:** regions are drawn as circles placed at their approximate centre.
"""
        )