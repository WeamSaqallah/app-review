# 📊 Market Intelligence & Competitor Scraping Tool

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-5.20+-3F4F75.svg)](https://plotly.com/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3-003B57.svg)](https://www.sqlite.org/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini-8E75C2.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end, enterprise-grade **Market Intelligence & Competitor Research System** that discovers competing mobile apps directly from the **Google Play Store**, extracts and normalizes hundreds of real customer reviews safely, categorizes feedback sentiment, persists relational data into **SQLite**, generates an automated multi-sheet **Excel report**, and feeds 1-star and 2-star friction points into **Google Gemini LLM** for executive-level market gap analysis.

---

## 🌟 Key Features & Deliverables

1. **Dynamic App Discovery**:
   - Search by application name, category, or niche keyword (e.g., *"food delivery"*, *"fitness tracker"*, *"habit tracker"*).
   - Real-time search returning app icon, title, developer, store rating, and Google Play Store link.

2. **Multi-App Selection & Targeted Scraping**:
   - Interactive selection of **2 to 4 competitors** via checkboxes.
   - Reliable extraction of **150–300 customer reviews per app** without memory bottlenecks or IP blocks.
   - Built with `google-play-scraper` using pagination and timestamp parsing.

3. **Data Pipeline, Cleaning & Sentiment Categorization**:
   - HTML entity decoding, whitespace normalization, and text cleansing.
   - Ground-truth sentiment categorization:
     - 🟢 **Positive**: 4–5 Stars
     - ⚪ **Neutral**: 3 Stars
     - 🔴 **Negative**: 1–2 Stars
   - Relational persistence in local SQLite database (`competitor_intelligence.db`) with indexed query performance.

4. **Strategic Market Gap Analysis (AI-Powered with Google Gemini)**:
   - Filters high-impact 1-star and 2-star complaints weighted by user upvotes (`thumbs_up_count`).
   - Generates an executive-level summary identifying:
     - 🚨 **Top Recurring Bugs & UX Friction** across competitors.
     - 💡 **Unmet Customer Desires** (features users are begging for that competitors lack).
     - 🎯 **Strategic Product Directives** for Day 1 development.
     - ⚡ **"Trojan Horse" Go-To-Market Feature** to trigger viral user migration.

5. **Interactive Client Dashboard (Streamlit & Plotly)**:
   - Modern, executive UI designed for non-technical stakeholders and product managers.
   - High-impact KPI metric cards (Total Analyzed, Sample Rating, Negative Feedback Ratio).
   - Grouped & stacked **Plotly charts** comparing sentiment share and rating distributions.
   - Grievance scatter plot correlating user upvotes with review dates.

6. **Automated Multi-Sheet Excel Report**:
   - Styled using `openpyxl` with navy/teal themes, auto-adjusted column widths, and cell borders.
   - **Sheet 1**: *Competitor Overview* (KPI comparison, sentiment breakdown percentages).
   - **Sheet 2**: *Sentiment Matrix* (Crosstab summary across competitors).
   - **Sheet 3**: *Pain Points (1–2 Stars)* (Filtered negative reviews sorted by community upvotes).
   - **Sheet 4**: *All Reviews Detail* (Comprehensive cleaned dataset).
   - Direct 1-click download from the web interface.

---

## 🏗️ Technical Architecture & Project Structure

```
Final_Project/
├── app.py                      # Main Streamlit client dashboard with Plotly charts & controls
├── market_engine.py            # Scraping engine, data cleaning, SQLite storage, Excel generation
├── market_ai.py                # Gemini LLM integration (google-genai) & strategic prompt engineering
├── competitor_intelligence.db  # Relational SQLite database (auto-generated upon execution)
├── requirements.txt            # Conflict-free dependency specifications
├── README.md                   # Comprehensive project documentation
└── proposal_draft.md           # Professional freelance proposal for live bidding
```

### Relational Database Schema (`competitor_intelligence.db`)

```sql
CREATE TABLE apps (
    app_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    developer TEXT,
    store_score REAL,
    scraped_avg_score REAL,
    scraped_reviews_count INTEGER,
    positive_pct REAL,
    neutral_pct REAL,
    negative_pct REAL,
    icon_url TEXT,
    last_updated TEXT
);

CREATE TABLE reviews (
    review_id TEXT PRIMARY KEY,
    app_id TEXT NOT NULL,
    app_title TEXT,
    user_name TEXT,
    score INTEGER,
    sentiment TEXT,
    content TEXT,
    clean_content TEXT,
    thumbs_up_count INTEGER,
    review_version TEXT,
    review_timestamp TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (app_id) REFERENCES apps(app_id)
);
```

---

## 🚀 Quick Start & Installation

### 1. Prerequisites
- Python 3.10 or higher.
- A Google Gemini API key (optional, can be obtained free from [Google AI Studio](https://aistudio.google.com/)).

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/google-play-competitor-intelligence.git
cd google-play-competitor-intelligence
```

### 3. Create and Activate a Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Gemini API Key (Optional but Recommended)
Set your environment variable or enter it directly in the dashboard's sidebar:
```bash
# Windows (PowerShell)
$env:GEMINI_API_KEY="your-gemini-api-key"

# macOS / Linux
export GEMINI_API_KEY="your-gemini-api-key"
```

### 6. Run the Streamlit Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🌐 Deploying to Streamlit Community Cloud

1. Push this repository to **GitHub**.
2. Visit [share.streamlit.io](https://share.streamlit.io/) and log in with your GitHub account.
3. Click **"New App"** and select:
   - **Repository**: Your repository name
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. In **Advanced Settings**, add your secret key:
   ```toml
   GEMINI_API_KEY = "your-api-key-here"
   ```
5. Click **Deploy!** Your app is now live with a shareable URL.

---

## 📊 Sample Screenshots & Workflow

1. **Search**: Enter keyword (e.g. `food delivery`) to fetch matching applications.
2. **Select**: Select between 2 and 4 competing apps.
3. **Analyze**: Click `🚀 Scrape & Run Analysis Pipeline`.
4. **Inspect**: Review Plotly graphs, read the Gemini executive market gap breakdown, and download the styled Excel report.

---

## 📜 License
This project is licensed under the MIT License - feel free to use and adapt for commercial or educational purposes.
