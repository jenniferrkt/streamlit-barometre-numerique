# Are we too online?

**Social media and digital wellbeing in France, 2023-2025.**
An individual Streamlit data-storytelling project, EFREI Paris .

How often do people in France check a social network? Does heavy use feel like too much time on screens?
And what do young people come across online that they did not look for? This dashboard follows these three
questions with one open dataset, and is honest about what a survey can and cannot say.

- **Live app:** https://app-barometre-numerique-cejzdwuzgvjkoumtq5mydi.streamlit.app/
- **Code:** jenniferrkt
- **Storyboard:** https://drive.google.com/file/d/1staZZKj66OTBPh-VzdpjKCRGXeYwHGwO/view?usp=sharing
- **Demo video (2-4 min):** https://drive.google.com/file/d/11rdivpBpafnusrSYLJv0SlFG9tEpamOC/view?usp=sharing
  
## The story in the app

1. **Why this matters subject matters -** with a short hook, the three questions we ask, and how to read the figures.
2. **Overview -** three key figures that follow the filters and a chart of social network use over time.
3. **Deep dives -** four different charts: does age make a difference, does where you live matter, do heavy users feel they spend too much time on screens, and what do people come across without looking for it.
4. **How far can we trust these numbers? -** data checks, missing answers and what to keep in mind.
5. **Key insights and next steps -** what we found, what it means for educators, parents and decision-makers, and its limits.

The filters in the sidebar (age focus, sex, region, survey years and the measure shown) change the charts.
Every chart has a sentence that gives its message, hover tooltips, labelled axes and a short text description.

## Data

| | |
|---|---|
| Dataset | [Baromètre du Numérique](https://www.data.gouv.fr/datasets/barometre-du-numerique) |
| Producer | ARCEP, with CGE, ANCT and Arcom; fieldwork by Crédoc |
| Portal | data.gouv.fr |
| Licence | [Open Database License (ODbL)](http://opendatacommons.org/licenses/odbl/summary/) |
| File used | CSV with all surveys from 2007 to 2025 (about 256 MB, 49,690 respondents, 1,195 columns) |
| Data dictionary | [Excel dictionary on data.gouv.fr](https://www.data.gouv.fr/api/1/datasets/r/cddd8615-e5ee-4f88-af0f-48ebec877c10) |

Citation: *Arcep, Arcom, CGE, ANCT, Baromètre du numérique, data.gouv.fr (ODbL).*

**What we use -** The questions about social networks only exist from 2023, so the app uses 2023, 2024 and 2025
(12,495 respondents). The three questions behind the story are:

| Question (variable) | Years |
|---|---|
| How often do you check a social network? (`RESOC`) | 2023-2025, online sample only |
| Do you spend too much time on your screens? (`OPITPSECRAN`) | 2024 |
| Did you come across inappropriate content without looking for it? (`INAPPRO_1` to `INAPPRO_8`) | 2025 |

A longer series (2009-2022) asks whether people used a social network at all (`US_FACEB`). It is a different
question, so it is shown in its own chart and never joined to the recent years.

The file only has six age groups (12-17, 18-24, 25-39, 40-59, 60-69, 70+), so the category "young people" means 12-24.

## Run it on your computer

You need Python 3.12 or newer (tested on 3.13).

```bash
python -m venv .venv
.venv\Scripts\activate          # on Mac or Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The small prepared data files are already in the `data/` folder (`barometre_extract_2023_2025.parquet`,
`social_participation_2009_2022.parquet` and `quality_report.json`), so the app starts straight away.
To rebuild them from the original source:

```bash
python scripts/build_data.py              # downloads the CSV into data/raw/ (once), then builds the files
python scripts/build_data.py --csv PATH   # or use a CSV file you already downloaded
```

## How the project is organised

```
app.py                  main page: look and feel, sidebar filters, order of the sections
config.py               file paths, data source, list of columns, English labels for the answers
sections/               one file per part of the story: intro, overview, deep_dives, data_quality, conclusions
utils/io.py             download the data once (with a cache) and load it
utils/prep.py           cleaning, translation, data checks, weighted percentages and margins of error
utils/viz.py            all the charts, so they share the same look
scripts/build_data.py   downloads the source file and builds the small data files
data/                   the small prepared data files (the big source file is not saved in git)
.streamlit/config.toml  colours of the Light and Dark themes
requirements.txt        exact versions of the libraries
```

## How it works

- `build_extract` reads 22 of the 1,195 columns, keeps 2023-2025 and saves a small file (about 1,100 times lighter than the CSV). `prepare` translates the answers into English and turns them into simple 0/1 columns when the app starts. The result is kept in memory with `st.cache_data`, so the app stays fast.
- If the source file contains an answer we do not know, the app stops with an error instead of
quietly treating it as missing.
- Every percentage uses the survey weight (`POND`), so the sample matches the French population. People who answered "don't know" or gave no answer are left out and counted in the data quality section.
- We use 95% Wilson intervals, based on the effective sample size. This takes unequal weights into account but not how the sample was drawn, so the margins are approximate. 
- There is no random sampling as the same file always gives the same figures.

## Accessibility

- Every chart has labelled axes and units, and a sentence below it that describes what it shows.
- The colours were chosen to stay readable in Light and Dark mode
- The text of each chart switches with the theme, so the labels and values stay easy to read.

## Limits and ethics

- These are opinions not measures. Nothing here shows that social media causes anything, and the app
says so.
- Questions about social networks were only put to people online, so the results describe internet users.
- Each year interviews different people, so we compare groups and years, never the same individuals over time.
- Some groups are small: about 200 respondents per year are aged 12-17, and Corse has fewer than 50 answers over the three years. The charts show the number of respondents and the margin of error.
- The app only shows groups of people, never individual respondents.

## Deployment (Streamlit Community Cloud)

1. Put this folder in a public GitHub repository (the small data files are included, `data/raw/` is not).
2. On share.streamlit.io, choose the repository, the `main` branch and `app.py`, then select Python 3.13.
3. Deploy. No secret key is needed.
