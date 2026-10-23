"""Cleaning the data, translating it, checking it, and computing the percentages shown in the app.
 
The work is done in two steps, kept apart on purpose:
 
1. build_extract() runs once. It reads only the columns we need from the big source file (256 MB),
   keeps the years 2023 to 2025, and saves a small file plus a quality report about the full source file.
2. prepare() runs when the app starts. It translates the answers into English and turns them into
   simple 0/1 columns (for example "checks a social network several times a day": 1 or 0).
 
The last part of the file holds the weighted percentages and margins of error used by every chart.
"""
import json
import math
from pathlib import Path
 
import numpy as np
import pandas as pd
 
import config as cfg
 
# build the small data file from the big source file
def build_extract(raw_csv, out_parquet, out_report):
    """Read the columns we need from the source file, then save the small data file and the quality report."""
    raw_csv, out_parquet, out_report = Path(raw_csv), Path(out_parquet), Path(out_report)
    header = pd.read_csv(raw_csv, nrows=0).columns.tolist()
    missing = [c for c in cfg.SOURCE_COLUMNS if c not in header]
    if missing:
        raise ValueError(f"Columns missing from the source file: {missing}")
 
    columns = list(dict.fromkeys(cfg.SOURCE_COLUMNS + cfg.ADOPTION_COLUMNS))
    df = pd.read_csv(raw_csv, usecols=columns, low_memory=False)
    years = sorted(int(y) for y in df["ANNEE"].unique())
    report = {
        "source": {
            "title": cfg.DATASET_TITLE,
            "page": cfg.DATASET_PAGE,
            "url": cfg.DATA_URL,
            "licence": cfg.LICENSE_NAME,
            "file": raw_csv.name,
            "size_bytes": raw_csv.stat().st_size,
        },
        "raw": {
            "rows": int(len(df)),
            "columns": int(len(header)),
            "columns_read": int(len(columns)),
            "years": years,
            "years_without_wave": [
                y for y in range(years[0], years[-1] + 1) if y not in years
            ],
            "duplicate_ident": int(df["IDENT"].duplicated().sum()),
            "weight_nulls": int(df["POND"].isna().sum()),
        },
    }
 
    extract = df.loc[df["ANNEE"] >= cfg.FIRST_YEAR, cfg.SOURCE_COLUMNS].reset_index(drop=True)
    out_parquet.parent.mkdir(parents=True, exist_ok=True)
    extract.to_parquet(out_parquet, index=False, compression="zstd")
    report["extract"] = {
        "rows": int(len(extract)),
        "columns": int(extract.shape[1]),
        "years": sorted(int(y) for y in extract["ANNEE"].unique()),
        "first_year": cfg.FIRST_YEAR,
        "file": out_parquet.name,
    }
 
    # The long series (2009-2022) has a single question, so it is saved in its own small file.
    adoption = df.loc[df["US_FACEB"].notna(), cfg.ADOPTION_COLUMNS].reset_index(drop=True)
    adoption.to_parquet(out_parquet.with_name(cfg.ADOPTION_PARQUET.name), index=False, compression="zstd")
    report["adoption"] = {
        "rows": int(len(adoption)),
        "years": sorted(int(y) for y in adoption["ANNEE"].unique()),
        "file": cfg.ADOPTION_PARQUET.name,
    }
    out_report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
 
 
# translate and prepare the data for the app
def _clean_text(s):
    """Make the text uniform (same apostrophe, single spaces) so the answers can be matched safely."""
    return (
        s.astype("string")
        .str.replace("’", "'", regex=False)
        # we list the special spaces by hand, because \s alone misses some of them (U+00A0, U+202F, U+2009)
        .str.replace("[\\s   ]+", " ", regex=True)
        .str.strip()
    )
 
 
def recode(s, mapping, order=None, name=""):
    """Translate the French answers into English, using `mapping` (French -> English).
 
    Safety check: if the file contains an answer that is not in `mapping`, we stop with an error
    instead of quietly leaving it empty. This way a change in the source file can never
    change the results without us noticing.
    If `order` is given, the answers keep that order (useful to sort the charts).
    """
    clean = _clean_text(s)
    unknown = sorted(set(clean.dropna().unique()) - set(mapping))
    if unknown:
        raise ValueError(f"{name or s.name}: unmapped source values {unknown}")
    out = clean.map(mapping).astype(object)
    if order is not None:
        return pd.Series(pd.Categorical(out, categories=order, ordered=True), index=s.index)
    return out
 
 
def indicator(cat, positives):
    """Give 1 if the answer is one of `positives`, 0 if it is not, and leave it empty if there is no answer."""
    out = cat.isin(list(positives)).astype("float64")
    return out.where(cat.notna(), np.nan)
 
 
def prepare(extract):
    """Turn the small data file into the clean table used by the app."""
    df = pd.DataFrame(index=extract.index)
    df["year"] = extract["ANNEE"].astype("int16")
    df["mode"] = extract["RECUEIL"].map({"CAWI": "online", "CATI": "phone"})
    df["weight"] = extract["POND"].astype("float64")
 
    df["age_group"] = recode(extract["AGE6FUZ"], cfg.AGE_MAP, cfg.AGE_ORDER, "AGE6FUZ")
    df["youth"] = df["age_group"].isin(cfg.YOUTH_AGES)
    df["sex"] = recode(extract["SEXE"], cfg.SEX_MAP, cfg.SEX_ORDER, "SEXE")
    df["region"] = recode(extract["REGION"], cfg.REGION_MAP, name="REGION")
 
    # Part 1: how often people use social networks
    df["social_freq"] = recode(
        extract["RESOC"], cfg.SOCIAL_FREQ_MAP, cfg.SOCIAL_FREQ_ORDER, "RESOC"
    )
    df["freq_group"] = df["social_freq"].map(cfg.FREQ_GROUPS).astype(
        pd.CategoricalDtype(cfg.FREQ_GROUP_ORDER, ordered=True)
    )
    df["sm_multi_daily"] = indicator(df["social_freq"], ["Several times a day"])
    df["sm_daily"] = indicator(
        df["social_freq"], ["Several times a day", "Daily or almost daily"]
    )
    for src, dst in cfg.ACTIVITY_COLUMNS.items():
        df[dst] = recode(extract[src], cfg.ACTIVITY_FREQ_MAP, cfg.ACTIVITY_FREQ_ORDER, src)
 
    # Part 2: how people feel about their screen time (2024)
    df["screen_opinion"] = recode(
        extract["OPITPSECRAN"], cfg.SCREEN_OPINION_MAP, cfg.SCREEN_OPINION_ORDER, "OPITPSECRAN"
    )
    df["screen_too_much"] = indicator(df["screen_opinion"], cfg.SCREEN_TOO_MUCH)
    df["screen_hours"] = recode(
        extract["HR_ECRAN2_7"], cfg.SCREEN_HOURS_MAP, cfg.SCREEN_HOURS_ORDER, "HR_ECRAN2_7"
    )
 
    # Part 3: unwanted content people come across (2025)
    for k in cfg.INAPPRO_ITEMS:
        col = f"inappro{k}"
        df[col] = recode(
            extract[f"INAPPRO_{k}"], cfg.EXPOSURE_MAP, cfg.EXPOSURE_ORDER, f"INAPPRO_{k}"
        )
        df[f"{col}_often"] = indicator(df[col], ["Often", "Sometimes"])
        df[f"{col}_ever"] = indicator(df[col], ["Often", "Sometimes", "Rarely"])
    return df
 
 
def prepare_adoption(adoption):
    """Prepare the long series: use of social networks from 2009 to 2022."""
    df = pd.DataFrame(index=adoption.index)
    df["year"] = adoption["ANNEE"].astype("int16")
    df["weight"] = adoption["POND"].astype("float64")
    df["age_group"] = recode(adoption["AGE6FUZ"], cfg.AGE_MAP, cfg.AGE_ORDER, "AGE6FUZ")
    df["sex"] = recode(adoption["SEXE"], cfg.SEX_MAP, cfg.SEX_ORDER, "SEXE")
    answer = recode(adoption["US_FACEB"], cfg.ADOPTION_MAP, name="US_FACEB")
    df["participates"] = indicator(answer, ["Yes"])
    df.loc[answer.isna(), "participates"] = np.nan  # "don't know" answers are left out
    return df
 
 
# Data quality tables (shown in the app)
_QUALITY_VARIABLES = {
    "REGION": "Region",
    "SEXE": "Sex",
    "AGE6FUZ": "Age group",
    "RESOC": "Social network use frequency",
    "RSFREQ1": "Posts own content",
    "RSFREQ2": "Shares / comments",
    "RSFREQ3": "Reads others' content",
    "OPITPSECRAN": "Perceived screen time",
    "HR_ECRAN2_7": "Weekly screen hours",
    **{f"INAPPRO_{k}": f"Exposure: {v}" for k, v in cfg.INAPPRO_ITEMS.items()},
}
 
 
def missingness_tables(extract):
    """For each question and each year, give two things: who was asked, and who did not answer.
 
    `asked` = the share of respondents who have a value. A blank means the question was not put to that
    person (another year, or another way of doing the survey). That is different from a "no answer".
    """
    asked, nonresp = {}, {}
    for col, label in _QUALITY_VARIABLES.items():
        by_year = extract.groupby("ANNEE")[col]
        asked[label] = by_year.apply(lambda s: s.notna().mean() * 100)
        nonresp[label] = by_year.apply(
            lambda s: (s.dropna().isin(cfg.NON_RESPONSE_VALUES).mean() * 100) if s.notna().any() else np.nan
        )
    asked_df = pd.DataFrame(asked).T
    nonresp_df = pd.DataFrame(nonresp).T
    for t in (asked_df, nonresp_df):
        t.columns = [int(c) for c in t.columns]
        t.index.name = "Question"
    return asked_df.round(1), nonresp_df.round(1)
 
 
def validation_checks(extract, analysis, report, adoption):
    """Run the data checks and return them as a table."""
    checks = []
 
    def add(name, ok, detail):
        checks.append({"Check": name, "Result": "Passed" if ok else "Failed", "Details": detail})
 
    raw = report["raw"]
    add("No duplicated respondents (full source file)", raw["duplicate_ident"] == 0,
        f"{raw['duplicate_ident']} duplicates among {raw['rows']:,} answers")
    add("Every respondent has a survey weight", raw["weight_nulls"] == 0,
        f"{raw['weight_nulls']} missing")
    add("No duplicated respondents (years used here)", not extract["IDENT"].duplicated().any(),
        f"{len(extract):,} answers kept for {cfg.FIRST_YEAR}-{cfg.YEARS[-1]}")
    add("No respondent counts for zero or less", bool((analysis["weight"] > 0).all()),
        f"weights range from {analysis['weight'].min():.2f} to {analysis['weight'].max():.2f}")
    means = analysis.groupby("year")["weight"].mean()
    add("Average weight is 1 each year, so totals stay realistic", bool(means.between(0.95, 1.05).all()),
        ", ".join(f"{y}: {m:.2f}" for y, m in means.items()))
    add(f"All years {cfg.YEARS[0]}-{cfg.YEARS[-1]} are present", sorted(analysis["year"].unique()) == list(cfg.YEARS),
        ", ".join(str(y) for y in sorted(analysis["year"].unique())))
    complete = ["age_group", "sex", "region"]
    nulls = {c: int(analysis[c].isna().sum()) for c in complete}
    names = {"age_group": "age", "sex": "sex", "region": "region"}
    add("Age, sex and region are always filled in", sum(nulls.values()) == 0,
        ", ".join(f"{names[c]}: {n} missing" for c, n in nulls.items()))
    cati = analysis[analysis["mode"] == "phone"]
    add("Social network questions only asked to people online",
        bool(cati["social_freq"].isna().all()),
        f"{len(cati):,} phone respondents, none asked")
    q = {
        "Screen time question asked in 2024 only":
            set(analysis.loc[analysis["screen_opinion"].notna(), "year"]) == {2024},
        "Unwanted content questions asked in 2025 only":
            set(analysis.loc[analysis["inappro1"].notna(), "year"]) == {2025},
    }
    for name, ok in q.items():
        add(name, ok, "matches the survey documentation")
    years = sorted(adoption["year"].unique())
    add("Long series 2009-2022 is complete",
        bool((adoption["weight"] > 0).all()) and years == list(range(2009, 2021)) + [2022],
        f"{len(adoption):,} answers over {len(years)} years ({years[0]}-{years[-1]}, no survey in 2021)")
    return pd.DataFrame(checks)
 
 
def make_tables(extract, analysis, report, adoption):
    """Prepare the tables for the data quality section, so they are not recomputed each time."""
    asked, nonresp = missingness_tables(extract)
    return {
        "checks": validation_checks(extract, analysis, report, adoption),
        "asked": asked,
        "nonresponse": nonresp,
    }
 
 
# Weighted statistics (used by every figure in the app)

# Each respondent has a weight (POND): it says how many people they stand for in the population.
# A weighted share is the total weight of the people who said "yes", divided by the total weight of
# everyone who answered.
#
# The margin of error is a 95% Wilson interval, computed on the "effective sample size" (n_eff).
# When weights are very unequal, the sample is worth fewer people than it actually contains,
# and n_eff measures that. The method ignores how the survey sample was drawn,
# so the margins are approximate.
 
def wilson_ci(p, n, z=1.96):
    """Margin of error (95% Wilson interval) for a share `p` between 0 and 1, measured on `n` people."""
    if n is None or not n > 0 or math.isnan(p):
        return float("nan"), float("nan")
    denominator = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    return centre - half, centre + half
 
 
def _share_of_group(group, flag):
    """Weighted share, margin of error and sample sizes for one group of respondents."""
    valid = group[group[flag].notna()]  # people who did not answer are left out
    weights = valid["weight"]
    if weights.sum() == 0:
        return {"share": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                "n": 0, "n_eff": float("nan")}
    share = (weights * valid[flag]).sum() / weights.sum()
    n_eff = weights.sum() ** 2 / (weights**2).sum()
    low, high = wilson_ci(share, n_eff)
    return {"share": share, "ci_low": low, "ci_high": high, "n": len(valid), "n_eff": n_eff}
 
 
def weighted_share(df, flag, by=None):
    """Weighted share of the 0/1 column `flag`, for everyone or for each value of the column `by`.
 
    Returns a table with one row per group and these columns:
    share (between 0 and 1), ci_low and ci_high (the margin of error), n (number of answers)
    and n_eff (effective sample size).
    """
    if by is None:
        return pd.DataFrame([_share_of_group(df, flag)])
    rows = []
    for key, group in df.groupby(by, observed=True):
        rows.append({by: key, **_share_of_group(group, flag)})
    return pd.DataFrame(rows)
 
 
def summarize(df, flag):
    """Weighted share for everyone, as a simple dictionary (used for the key figures)."""
    result = _share_of_group(df, flag)
    if result["n"] == 0:
        result["n_eff"] = 0.0
    return result
 