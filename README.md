# 📊 EconIQ — Economic Intelligence Assistant

> RAG-powered financial and economic Q&A built entirely on Snowflake.  
> Ask plain-English questions. Get cited answers in seconds.

[![Snowflake](https://img.shields.io/badge/Built%20on-Snowflake-29B5E8?style=flat&logo=snowflake)](https://snowflake.com)
[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://python.org)
[![Streamlit](https://img.shields.io/badge/UI-Streamlit-FF4B4B)](https://streamlit.io)

---

## 🏆 TAMU CSEGSA × Snowflake Hackathon 2026

**Track:** AI Track — Prompt 01 (RAG Knowledge Assistant)  
**Team:**

| Name | Email | University |
|---|---|---|
| Ishant Kundra | ishantkundra9@gmail.com | Texas A&M University (MS CS, May 2025) |
| Tanishq Chopra | tanishqtc1980@gmail.com | Texas A&M University |

**GitHub:** https://github.com/tanishq-chopra1/EconAI---Economic-Intelligence-Assistant-SnowFlake-Hackathon-

---

## 🖥️ Demo

![EconIQ Demo](demo.png)

---

## 📌 What it does

Financial analysts spend hours manually searching SEC filings, Fed reports,
World Bank databases, and CFPB complaint logs. EconIQ answers those same
questions in seconds — with inline citations on every claim.

| Without EconIQ | With EconIQ |
|---|---|
| Search SEC EDGAR manually | Ask in plain English |
| Download Fed Reserve CSVs | Get cited answers in seconds |
| Query World Bank API separately | 14 datasets unified |
| Cross-reference CFPB complaints | Zero external APIs — 100% Snowflake |
| Hours of analyst time | Auditable citations on every answer |

---

## 🏗️ RAG Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SNOWFLAKE MARKETPLACE                           │
│  SEC Filings · Fed Reserve · World Bank · CFPB · FEMA · OECD · ... │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ 14 source tables
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     INGESTION (Snowpark Python)                     │
│                                                                     │
│   Part A — Text Tables          Part B — Numeric Narrativization    │
│   ┌─────────────────────┐       ┌─────────────────────────────┐    │
│   │ Transcripts         │       │ Fed Reserve timeseries  →   │    │
│   │ SEC 10-K / 10-Q     │       │ World Bank timeseries   →   │    │
│   │ CFPB Complaints     │  +    │ OECD timeseries         →   │    │
│   │ Gov Contracts       │       │ US Treasury timeseries  →   │    │
│   │ FEMA Disasters      │       │ FHFA House Prices       →   │    │
│   │ WB Indicators       │       │ DOL Unemployment        →   │    │
│   └─────────────────────┘       │   Natural Language          │    │
│   400-word chunks               │      Sentences              │    │
│   60-word overlap               └─────────────────────────────┘    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ 209,451 chunks
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              HACKATHON.DATA.CHUNKS (Snowflake Table)                │
│         CHUNK_ID · CHUNK_TEXT · SOURCE · TITLE · METADATA          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│           CORTEX SEARCH SERVICE (Arctic Embed)                      │
│     Semantic + full-text hybrid search · Auto-vectorized            │
│              HACKATHON.DATA.RAG_SEARCH                              │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
          ┌────────────────────┴────────────────────┐
          │         USER ASKS A QUESTION            │
          │    "What risks do US banks disclose?"   │
          └────────────────────┬────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │  Cortex Search   │  ← retrieve top-k chunks
                    │  (Arctic Embed)  │
                    └────────┬─────────┘
                             │ top-k chunks with citations
                             ▼
                    ┌──────────────────┐
                    │ Grounded Prompt  │  ← context + question
                    │    Builder       │     + length instruction
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │ Cortex COMPLETE  │  ← mistral-large
                    │  (Generation)    │
                    └────────┬─────────┘
                             │
                             ▼
          ┌────────────────────────────────────────┐
          │         CITED ANSWER                   │
          │  "US banks disclose liquidity risk     │
          │   as the inability to meet financial   │
          │   obligations [1]. Credit risk arises  │
          │   from lending activities [2]..."      │
          │                                        │
          │  🟢 Confidence: 90%                    │
          │  📎 5 sources used                     │
          └────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  STREAMLIT IN SNOWFLAKE                             │
│   4-tab UI · Source filter · Response length · Citation panel      │
└─────────────────────────────────────────────────────────────────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────────┐   ┌──────────────┐
│    Model     │   │   Feature Store  │   │  Eval Table  │
│  Registry   │   │ CHUNK_FEATURES   │   │ EVAL_RESULTS │
│ ECONIQ_RAG  │   │      v1          │   │  20/20 ✅    │
│     v1      │   └──────────────────┘   └──────────────┘
└──────────────┘
```

---

## 💡 Key Innovation: Numeric Narrativization

Standard RAG systems can only retrieve text. EconIQ converts 6 numeric
time-series datasets into natural language sentences before indexing:

```
"Federal funds rate (country/USA): As of 2024-09-30, the value was 5.33%.
It decreased from 5.58% in the prior period. From 2018-01-31 to 2024-09-30,
total change was +433.0%. Recent readings: 5.33, 5.33, 5.33, 5.58, 5.33."
```

This enables semantic retrieval over quantitative data — a capability not
present in standard RAG implementations.

**Narrativized sources:** Federal Reserve · World Bank · OECD · US Treasury · FHFA · DOL Unemployment

---

## 📊 Corpus — 209,451 chunks across 14 sources

| Source | Chunks | Type |
|---|---|---|
| TRANSCRIPT | 116,559 | Earnings call transcripts |
| SEC_10K | 17,955 | 10-K annual filings |
| FED_RESERVE | 16,201 | Federal Reserve narratives |
| ECON_INDICATORS | 12,791 | Economic indicator narratives |
| WORLD_BANK | 12,133 | World Bank narratives |
| SEC_10Q | 8,973 | 10-Q quarterly filings |
| GOV_CONTRACT | 7,223 | Government contract descriptions |
| CFPB_COMPLAINT | 5,769 | Consumer complaint narratives |
| FEMA_DISASTER | 5,000 | FEMA disaster declarations |
| OECD | 4,251 | OECD indicator narratives |
| WB_INDICATOR | 1,680 | World Bank definitions |
| FHFA_HOUSING | 511 | Housing price narratives |
| MORTGAGE | 367 | State-level mortgage narratives |
| US_TREASURY | 38 | Treasury yield narratives |
| **Total** | **209,451** | |

---

## 📈 Evaluation Results

- **20/20** questions answered
- **10.0** avg citations per answer
- **85%** avg confidence score
- Eval results saved to `HACKATHON.DATA.EVAL_RESULTS`
- Model logged to Snowflake Model Registry as `ECONIQ_RAG v1`
- Features registered in Snowflake Feature Store as `CHUNK_FEATURES v1`

---

## 🚀 Setup Instructions

### Prerequisites
- Snowflake trial account
- Warehouse: `HACKATHON_WH`
- Database: `HACKATHON`, Schema: `HACKATHON.DATA`

### Step 1 — Run SQL setup
Open `setup.sql` in a Snowflake SQL worksheet and run all statements.
This creates the database, schema, warehouse, and Cortex Search service.

### Step 2 — Run the notebook
Open `notebook.ipynb` in Snowflake Notebooks and run cells in order:

| Cell | Purpose |
|---|---|
| Cell 1 | Session setup + explore 20 source tables |
| Cell 2 | Inspect skip tables |
| Cell 3 | Verification queries |
| Cell 4 | Full ingestion — 209,451 chunks (~15 mins) |
| Cell 5 | Write chunks to HACKATHON.DATA.CHUNKS (~3 mins) |
| Cell 6 | RAG query function v1 + smoke test |
| Cell 7 | RAG query v2 with source filter |
| Cell 8 | Model Registry — log EconIQ_RAG v1 |
| Cell 9 | Verify Model Registry |
| Cell 10 | Feature Store — register CHUNK_FEATURES v1 |

> ⚠️ Cell 4 takes ~15 minutes. Do not interrupt it.

### Step 3 — Create Streamlit app
1. Go to **Projects → Streamlit → + Streamlit App**
2. Set Name: `EconIQ`, Database: `HACKATHON`, Schema: `DATA`
3. Paste contents of `streamlit_app.py`
4. Click **▶ Run**

---

## 📁 Repository Structure

```
├── README.md               # This file
├── setup.sql               # Database, schema, warehouse, Cortex Search setup
├── notebook.ipynb          # Data ingestion + Model Registry + Feature Store
├── streamlit_app.py        # EconIQ 4-tab Streamlit application
└── demo.png                # App screenshot
```

---

## ✨ App Features

- **4-tab interface** — Ask a Question, Eval Report, Data Sources, Architecture
- **Source filtering** — restrict retrieval to any of 14 datasets
- **Response length control** — Concise, Medium, or Lengthy responses
- **Confidence scoring** — every answer rated by citation count and response quality
- **Citation panel** — expandable sources with full text popover
- **Demo workflows** — one-click Bank Analyst, Fed Researcher, Mortgage Analyst personas
- **Conversation history** — multi-turn chat maintains context

---

## 🔑 Snowflake Platform Features Used

`Cortex Search` · `Arctic Embed` · `Cortex COMPLETE (mistral-large)` ·
`Snowpark Python` · `Streamlit in Snowflake` · `Model Registry` · `Feature Store` · `Snowflake Notebooks`

---

## ⚠️ Known Limitation

OECD data uses ISO country codes internally (`country/USA`, `country/KOR`).
Country-specific OECD queries work best with codes rather than full country names.

---

## 📞 Contact

**Ishant Kundra** — ishantkundra9@gmail.com · ishantkundra@tamu.edu  
**Tanishq Chopra** — tanishqtc1980@gmail.com · tanishq.chopra@tamu.edu  
Texas A&M University · TAMU CSEGSA × Snowflake Hackathon 2026
