"""Main page of the app: social media use and digital wellbeing in France, 2023-2025.
 
It loads the data, draws the filters in the sidebar, then shows the story one section at a time.
 
To start the app, run:  streamlit run app.py
"""
import streamlit as st
 
import config as cfg
from sections import conclusions, data_quality, deep_dives, intro, overview
from utils.io import load_adoption, load_extract
from utils.prep import make_tables, prepare, prepare_adoption
 
st.set_page_config(
    page_title="Social media and digital wellbeing in France",
    layout="wide",
)
 
# Look and feel, done with a bit of CSS. Two layout changes:
# 1. The sidebar sits on the right instead of the left (we flip the order of the page and the sidebar).
# 2. The top-right menu only keeps the Light / Dark choice, everything else is hidden.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Newsreader:wght@400;600&family=Source+Sans+3:wght@400;600&display=swap');
    /* fonts: serif for titles and big numbers, plain sans-serif for the rest */
    html, body, [data-testid="stApp"] { font-family: "Source Sans 3", sans-serif; }
    h1, h2, h3, [data-testid="stMetricValue"] { font-family: "Newsreader", Georgia, serif !important; }
    h1 { font-weight: 600; font-size: 3rem; letter-spacing: -0.01em; }
    h2 { border-top: 1px solid rgba(128,128,128,0.35); padding-top: 1.2rem; margin-top: 2.5rem; font-weight: 600; }
    /* key figures: big serif number with a small capital label */
    [data-testid="stMetric"] { padding: 0.2rem 0.3rem; }
    [data-testid="stMetricLabel"] { min-height: 2.4rem; align-items: flex-start; }
    [data-testid="stMetricLabel"] * { white-space: normal !important; overflow: visible !important; text-overflow: clip !important; }
    [data-testid="stMetricLabel"] p { text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.75rem; line-height: 1.3; }
    [data-testid="stSidebar"] [data-testid="stMetricValue"] { font-size: 2rem; }
    [data-testid="stMetricValue"] * { overflow: visible !important; text-overflow: clip !important; }  
    /* filters: small capital group titles, and the labels that summarise the selection */
    .filter-group { text-transform: uppercase; letter-spacing: 0.08em; font-size: 0.75rem; opacity: 0.7; margin: 1rem 0 0.2rem; }
    .chip { display: inline-block; border: 1px solid rgba(128,128,128,0.5); border-radius: 999px;
            padding: 0.1rem 0.7rem; margin: 0 0.4rem 0.4rem 0; font-size: 0.85rem; }
    /* cards: every container with a border becomes a rounded card */
    [class*="st-key-card"] {
        background: light-dark(#ffffff, #173a49) !important;
        border: 1px solid light-dark(transparent, #25536a) !important;
        box-shadow: 0 6px 20px light-dark(rgba(40, 70, 120, 0.10), transparent) !important;
        border-radius: 16px; padding: 0.6rem 0.9rem;
    }
    [class*="st-key-card"] h2, [class*="st-key-card"] h3 {
        border-top: none; margin-top: 0; padding-top: 0;
    }
    [data-testid="stSidebar"] input::placeholder { color: #ffffff !important; opacity: 0.85; }
    .chip.warn { border-color: #d98e04; background: rgba(245,158,11,0.14); }
    /* sidebar on the right, and a menu limited to Light / Dark */
    [data-testid="stAppViewContainer"] { flex-direction: row-reverse; }
    [data-testid="stAppDeployButton"] { display: none; }
    [data-testid="stMainMenuItem-theme-System"],
    [data-testid="stMainMenuItem-rerun"],
    [data-testid="stMainMenuItem-autoRerun"],
    [data-testid="stMainMenuItem-clearCache"],
    [data-testid="stMainMenuItem-print"],
    [data-testid="stMainMenuItem-recordScreencast"],
    [data-testid="stMainMenuDivider"],
    [data-testid="stMainMenuList"] + div { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)
# Streamlit does not rerun the app when someone switches between Light and Dark, so the charts would keep
# the old colours. A hidden button, clicked by a small script when the theme changes, forces a rerun.
st.markdown(
    "<style>.st-key-theme_rerun { position: absolute; left: -9999px; height: 0; overflow: hidden; }</style>",
    unsafe_allow_html=True,
)
st.button("Refresh theme", key="theme_rerun")
st.html(
    """
    <script>
    if (!window.themeWatch) {
        const scheme = () => getComputedStyle(document.querySelector('[data-testid="stApp"]')).colorScheme;
        let last = scheme();
        window.themeWatch = setInterval(() => {
            const now = scheme();
            if (now !== last) {
                last = now;
                const button = document.querySelector('.st-key-theme_rerun button');
                if (button) button.click();
            }
        }, 400);
    }
    </script>
    """,
    unsafe_allow_javascript=True,
)
 
 
@st.cache_data(show_spinner="Loading the survey data...")
def get_data():
    """Load the data once and prepare every table the app needs."""
    extract, report = load_extract()
    analysis = prepare(extract)
    adoption = prepare_adoption(load_adoption())
    tables = make_tables(extract, analysis, report, adoption)
    return analysis, adoption, tables, report
 
 
def build_sidebar(df):
    """Draw the filters in the sidebar and return what the person selected."""
    with st.sidebar:
        st.header("Filters")
        st.markdown('<div class="filter-group">Who</div>', unsafe_allow_html=True)
        focus = st.pills(
            "Age focus", list(cfg.AGE_FOCUS), default=list(cfg.AGE_FOCUS)[0],
        ) or list(cfg.AGE_FOCUS)[0]  # clicking the selected pill would clear it, so we fall back to the default
        ages = list(cfg.AGE_FOCUS[focus])
        sexes = st.pills("Sex", cfg.SEX_ORDER, selection_mode="multi", default=cfg.SEX_ORDER)
        st.markdown('<div class="filter-group">When</div>', unsafe_allow_html=True)
        years = st.select_slider(
            "Survey years",
            options=list(cfg.YEARS),
            value=(cfg.YEARS[0], cfg.YEARS[-1]),
        )
        st.markdown('<div class="filter-group">Where</div>', unsafe_allow_html=True)
        all_regions = sorted(df["region"].unique())
        regions = st.multiselect(
            "Region", all_regions, placeholder="All regions",
        ) or all_regions
        st.markdown('<div class="filter-group">What</div>', unsafe_allow_html=True)
        indicator = st.radio(
            "Measure for age and region charts",
            list(cfg.INDICATORS),
        )
        st.caption("Applies to the age chart and the map only.")
    return focus, years, ages, sexes, regions, indicator
 
 
analysis, adoption, tables, report = get_data()
 
st.markdown(
    '<div style="text-align: center">'
    '<h1 style="font-size: 4.8rem; line-height: 1.1; padding-bottom: 0">Are we '
    '<span style="color: light-dark(#e04848, #ee7b75)">too online?</span></h1>'
    '<div style="font-size: 1.6rem; opacity: 0.8">Social media and digital wellbeing in France, 2023-2025</div>'
    '<div style="font-size: 0.9rem; opacity: 0.65; margin-top: 0.6rem">'
    f"Source: {cfg.DATASET_TITLE} ({cfg.DATASET_PRODUCER}), data.gouv.fr, licence {cfg.LICENSE_NAME}. "
    f"Survey years {cfg.YEARS[0]}-{cfg.YEARS[-1]}.</div></div>",
    unsafe_allow_html=True,
)
 
focus, years, ages, sexes, regions, indicator = build_sidebar(analysis)
# a short line of labels that reminds the person which filters are on
chips = [focus, "All sexes" if len(sexes) == len(cfg.SEX_ORDER) else ", ".join(sexes),
         "All regions" if len(regions) == len(analysis["region"].unique()) else (regions[0] if len(regions) == 1 else f"{len(regions)} regions"),
         f"{years[0]}-{years[1]}" if years[0] != years[1] else str(years[0])]
st.markdown("".join(f'<span class="chip">{c}</span>' for c in chips if c), unsafe_allow_html=True)
 
if not (ages and sexes and regions):
    st.warning("Select at least one value in every filter to display results.")
    st.stop()
 
# `baseline` = everyone in the chosen years. `data` = the same people, narrowed by the other filters.
baseline = analysis[analysis["year"].between(*years)]
data = baseline[
    baseline["age_group"].isin(ages)
    & baseline["sex"].isin(sexes)
    & baseline["region"].isin(regions)
]
if data.empty:
    st.warning("No respondent matches these filters. Widen the selection in the sidebar.")
    st.stop()
 
# The 2009-2022 chart only uses the age and sex filters (the region was not recorded before 2020).
adoption_sel = adoption[adoption["age_group"].isin(ages) & adoption["sex"].isin(sexes)]
 
# The age chart keeps every age group: the age filter only highlights some of the bars.
by_age = baseline[baseline["sex"].isin(sexes) & baseline["region"].isin(regions)]
# The map keeps every region and every age, so it always shows the "all ages" picture.
by_region = baseline[baseline["sex"].isin(sexes)]
 
st.sidebar.metric("Respondents", f"{len(data):,}", f"of {len(analysis):,}", delta_color="off", delta_arrow="off") 
intro.render(analysis)
overview.render(data, baseline, adoption_sel, adoption)
deep_dives.render(by_age, ages, indicator, by_region, data, baseline)
data_quality.render(analysis, tables, report)
conclusions.render(analysis)
 
