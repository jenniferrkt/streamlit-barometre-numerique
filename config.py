"""Settings used everywhere in the app: file paths, where the data comes from, and the translations of the answers.
 
Everything that describes the dataset (links, licence, list of columns, English labels) is kept here,
so the other files do not need any hard-coded values.
"""
 
from pathlib import Path
 
# Paths
ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"  # git-ignored: the 256 MB raw CSV is never committed
RAW_CSV = RAW_DIR / "barometre-du-numerique-2007-2025.csv"
EXTRACT_PARQUET = DATA_DIR / "barometre_extract_2023_2025.parquet"
ADOPTION_PARQUET = DATA_DIR / "social_participation_2009_2022.parquet"
QUALITY_JSON = DATA_DIR / "quality_report.json"
 
# Source (data.gouv.fr)
DATASET_TITLE = "Baromètre du Numérique"
DATASET_PRODUCER = (
    "ARCEP (with CGE, ANCT and Arcom; fieldwork by Crédoc)"
)
DATASET_PAGE = "https://www.data.gouv.fr/datasets/barometre-du-numerique"
# Permanent data.gouv.fr links (they always point to the current file).
DATA_URL = "https://www.data.gouv.fr/api/1/datasets/r/d31629c2-3840-4aad-8380-a702af9b1d1f"
DICTIONARY_URL = "https://www.data.gouv.fr/api/1/datasets/r/cddd8615-e5ee-4f88-af0f-48ebec877c10"
LICENSE_NAME = "Open Database License (ODbL)"
LICENSE_URL = "http://opendatacommons.org/licenses/odbl/summary/"
 

# Scope
# The questions about social networks only exist from 2023.
FIRST_YEAR = 2023
YEARS = (2023, 2024, 2025)
MIN_N_EFF = 100  # below this effective sample size, the UI warns the reader
 
# The source file has 1,195 columns. We only read the ones listed here.
SOURCE_COLUMNS = [
    "IDENT", "ANNEE", "RECUEIL", "POND",
    "AGE6FUZ", "REGION", "SEXE",
    "RESOC", "RSFREQ1", "RSFREQ2", "RSFREQ3",
    "OPITPSECRAN", "HR_ECRAN2_7",
    *[f"INAPPRO_{i}" for i in range(1, 9)],
]
 
# Long series: "did you use a social network in the last 12 months?" (US_FACEB).
# It was asked from 2009 to 2022 (no survey in 2021) and is a different question from RESOC.
ADOPTION_COLUMNS = ["ANNEE", "POND", "AGE6FUZ", "SEXE", "US_FACEB"]
ADOPTION_MAP = {"Oui": "Yes", "Non": "No", "[Nsp]": None}
# From 2020 the survey is almost entirely online and about twice as large (see the data quality section).
ADOPTION_BREAK_YEAR = 2020
 
# Answers that are not a real answer: they count as "no answer", not as "never".
NON_RESPONSE_VALUES = ("Non réponse", "Ne sait pas")
 

# Translations: the survey answers are in French, the app is in English.

AGE_MAP = {
    "12-17 ans": "12-17",
    "18-24 ans": "18-24",
    "25-39 ans": "25-39",
    "40-59 ans": "40-59",
    "60-69 ans": "60-69",
    "70 ans et plus": "70+",
}
AGE_ORDER = ["12-17", "18-24", "25-39", "40-59", "60-69", "70+"]
YOUTH_AGES = ("12-17", "18-24")
 
# Choices for "Age focus" in the sidebar: label -> age groups kept (young people by default).
AGE_FOCUS = {
    "Youth (12-24)": YOUTH_AGES,
    "12-17 only": ("12-17",),
    "18-24 only": ("18-24",),
    "All ages (comparison)": tuple(AGE_ORDER),
}
 
# Choices for "Measure for age and region charts" in the sidebar: label -> column of the data.
INDICATORS = {
    "Social network use (several times a day)": "sm_multi_daily",
    "Feeling of spending too much time on screens": "screen_too_much",
    "Seeing self-harm content (often or sometimes)": "inappro5_often",
}
 
SEX_MAP = {"Femme": "Female", "Homme": "Male"}
SEX_ORDER = ["Female", "Male"]
 
REGION_MAP = {
    "Auvergne - Rhône Alpes": "Auvergne-Rhône-Alpes",
    "Bourgogne Franche Comté": "Bourgogne-Franche-Comté",
    "Bretagne": "Bretagne",
    "Centre Val de Loire": "Centre-Val de Loire",
    "Corse": "Corse",
    "Grand Est": "Grand Est",
    "Hauts de France": "Hauts-de-France",
    "Ile de France": "Île-de-France",
    "Normandie": "Normandie",
    "Nouvelle Aquitaine": "Nouvelle-Aquitaine",
    "Occitanie": "Occitanie",
    "PACA": "PACA",
    "Pays de la Loire": "Pays de la Loire",
}
# Approximate centre of each region (latitude, longitude), used to place the circles on the map.
# This way we do not need a second dataset with the region borders.
REGION_COORDS = {
    "Auvergne-Rhône-Alpes": (45.45, 4.65),
    "Bourgogne-Franche-Comté": (47.10, 4.80),
    "Bretagne": (48.15, -2.90),
    "Centre-Val de Loire": (47.55, 1.70),
    "Corse": (42.15, 9.10),
    "Grand Est": (48.70, 5.90),
    "Hauts-de-France": (50.05, 2.80),
    "Île-de-France": (48.70, 2.50),
    "Normandie": (49.10, 0.20),
    "Nouvelle-Aquitaine": (45.10, 0.20),
    "Occitanie": (43.70, 2.10),
    "PACA": (43.95, 6.05),
    "Pays de la Loire": (47.50, -0.80),
}
 
# How often people check a social network (RESOC), from most to least often.
SOCIAL_FREQ_MAP = {
    "Plusieurs fois par jour": "Several times a day",
    "Tous les jours ou presque": "Daily or almost daily",
    "1 à 2 fois par semaine": "1-2 times a week",
    "Plus rarement": "Less often",
    "Jamais": "Never",
    "Non réponse": None,
}
SOCIAL_FREQ_ORDER = [v for v in SOCIAL_FREQ_MAP.values() if v]
# Three groups for the screen-time chart. The rarer answers are merged so each group has enough respondents.
FREQ_GROUPS = {
    "Several times a day": "Several times a day",
    "Daily or almost daily": "Daily or almost daily",
    "1-2 times a week": "Less often or never",
    "Less often": "Less often or never",
    "Never": "Less often or never",
}
FREQ_GROUP_ORDER = ["Less often or never", "Daily or almost daily", "Several times a day"]
 
# How often people post, share or read on social networks (RSFREQ1-3).
ACTIVITY_FREQ_MAP = {
    "Plusieurs fois par jour": "Several times a day",
    "Tous les jours ou presque": "Daily or almost daily",
    "Une à deux fois par semaine": "1-2 times a week",
    "Moins souvent": "Less often",
    "Jamais": "Never",
    "Non réponse": None,
}
ACTIVITY_FREQ_ORDER = [v for v in ACTIVITY_FREQ_MAP.values() if v]
ACTIVITY_COLUMNS = {
    "RSFREQ1": "act_post",    # publish own content
    "RSFREQ2": "act_share",   # share / comment on others' content
    "RSFREQ3": "act_read",    # read others' content and comments
}
 
# How people feel about their own screen time (OPITPSECRAN, asked in 2024 only).
SCREEN_OPINION_MAP = {
    "Très peu de temps": "Very little",
    "Peu de temps": "Little",
    "Le temps qu'il faut": "About the right amount",
    "Trop de temps": "Too much",
    "Beaucoup trop de temps": "Far too much",
    "Non réponse": None,
}
SCREEN_OPINION_ORDER = [v for v in SCREEN_OPINION_MAP.values() if v]
SCREEN_TOO_MUCH = ("Too much", "Far too much")
 
# Hours spent on screens each week (HR_ECRAN2_7, asked in 2024 only).
SCREEN_HOURS_MAP = {
    "Aucune": "None",
    "7 heures ou moins (1h par jour ou moins)": "7 h or less",
    "De 8 à 14 heures": "8-14 h",
    "De 15 à 21 heures": "15-21 h",
    "De 22 à 35 heures": "22-35 h",
    "Plus de 35 heures par semaine (5h/jour)": "Over 35 h (5 h+/day)",
    "Ne sait pas": None,
}
SCREEN_HOURS_ORDER = [v for v in SCREEN_HOURS_MAP.values() if v]
 
# How often people come across unwanted content (INAPPRO_1 to 8, asked in 2025 only).
EXPOSURE_MAP = {
    "Souvent": "Often",
    "De temps en temps": "Sometimes",
    "Rarement": "Rarely",
    "Jamais": "Never",
    "Non réponse": None,
}
EXPOSURE_ORDER = [v for v in EXPOSURE_MAP.values() if v]
INAPPRO_ITEMS = {
    1: "Violent content",
    2: "Sexually explicit content",
    3: "Hateful or discriminatory content",
    4: "Insulting or vulgar content",
    5: "Suicide or self-harm content",
    6: "Eating-disorder content",
    7: "Animal cruelty",
    8: "Misinformation / fake news",
}
 