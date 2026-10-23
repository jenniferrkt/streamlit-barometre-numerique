"""Section 1: why this matters, the three questions we ask, and how to read the data."""
import streamlit as st
 
import config as cfg
from utils.prep import weighted_share
 
 
def _hook(analysis):
    return (
        "Picture a typical day in France. Before noon, 45% of people online have already checked a social "
        "network, and they will use it again several times in the day. By evening, 6 in 10 of the heaviest "
        "users feel they have spent too much time on their screens. And young people even run into unwanted "
        "content more often than anyone else in their feed. But how far can a survey go in explaining this?"
    )
 
def render(analysis):
    st.header("An important subject")
    st.markdown(_hook(analysis))
    questions = [
        ("1. Who is online most?", "How often people consult social networks, by age, sex and region."),
        ("2. Does heavy use feel like too much?", "Perceived screen time among frequent and occasional users (2024)."),
        ("3. What do people run into?", "Unwanted exposure to violent, hateful or self-harm content, by age (2025)."),
    ]
    for i, (col, (title, text)) in enumerate(zip(st.columns(3), questions)):
        with col.container(border=True, key=f"card_question{i}"):
            st.markdown(f"**{title}**  \n{text}")
 
    with st.expander("Who this is for, where the data comes from and how to read it", expanded=False):
        st.markdown(
            f"""
**Audience :** Educators, parents, and public-policy staff working on digital education.
 
**Data :** [{cfg.DATASET_TITLE}]({cfg.DATASET_PAGE}) ({cfg.DATASET_PRODUCER}), a yearly survey of
about 4,000 people aged 12 and over. This app uses the {cfg.YEARS[0]}-{cfg.YEARS[-1]} surveys, the only ones
that ask about social networks. 
 
Licence: [{cfg.LICENSE_NAME}]({cfg.LICENSE_URL}).
 
**How to read it :**
- Every percentage is weighted with the survey weights and shown with a 95 % confidence interval.
- The figures describe perceptions and self-reported experiences, not mental health, and they do not show that social media causes anything.
- "Too much time on screens" covers all screens, not only social networks. "Unwanted content" is what people
  say they came across without looking for it.
- Social-network questions were only put to the online sample, so results describe internet users.
"""
        )
 