# FinControl AI

FinControl AI is a finance-controls demonstration project for reconciliation, exception management, operational-risk scoring, and audit-ready reporting.

## What it demonstrates

- Reconciliation across payments, bank statements, and general ledger
- Determininistic control checks for missing, duplicate, delayed, FX, and classification issues
- Explainable risk scores and recommended next actions
- Isolation Forest anomaly scoring for unusual transaction patterns
- A Streamlit dashboard with executive, reconciliation, exception, anomaly, regulatory, and investigator views
- Curated CSV exports that can be loaded directly into Power BI

## Quick start

```powershell
python -m pip install -r requirements.txt
python -m src.generate_data
python -m src.pipeline
streamlit run app.py
```

The dashboard works with the generated data under `data/`. Pipeline outputs are written to `outputs/`.

## Power BI handoff

Load `outputs/exceptions.csv`, `outputs/reconciliation_summary.csv`, and `outputs/control_summary.csv` into Power BI. A suggested data model and measures are in [docs/powerbi.md](docs/powerbi.md).

## Project structure

```
app.py                 Streamlit dashboard
src/generate_data.py   Deterministic synthetic payments data generator
src/pipeline.py        Reconciliation, controls, risk, anomaly and export pipeline
data/                  Source-system CSV files (generated)
outputs/               Curated, audit-ready tables (generated)
docs/                  Dashboard and Power BI guidance
```

This project uses synthetic data only; it is not a production control framework.

## GitHub portfolio setup

Before publishing, replace `YOUR-USERNAME` in the suggested repository URL and add two screenshots from the dashboard to `docs/images/` (for example, the executive overview and exception explorer).

Recommended GitHub repository metadata:

- **Repository name:** `fincontrol-ai`
- **Description:** `AI-powered reconciliation, financial controls, and exception-risk analytics dashboard built with Python, Streamlit, and Power BI-ready data exports.`
- **Topics:** `finance`, `reconciliation`, `risk-analytics`, `streamlit`, `power-bi`, `anomaly-detection`, `python`, `fintech`

### Publish commands

```powershell
git add .
git commit -m "Build FinControl AI reconciliation dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/fincontrol-ai.git
git push -u origin main
```

Do not commit `.streamlit/secrets.toml`, API keys, bank data, or customer data. This repository intentionally contains synthetic data only.

## Demo talking points

1. The pipeline reconciles payments against bank and ledger records, then creates an auditable exception table.
2. Risk scores combine deterministic financial-control failures with an explainable anomaly signal.
3. The same curated outputs power the Streamlit dashboard and can be loaded directly into Power BI.
4. In a production version, the investigator would retrieve approved evidence and use an LLM with access controls and human review.
