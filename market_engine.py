"""
market_engine.py
================
Core data scraping, cleaning, normalization, relational storage (SQLite),
and Excel report generation module for the Market Intelligence & Competitor Scraping Tool.
"""

import io
import re
import html
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

from google_play_scraper import search, reviews, Sort

# Configure logging 
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MarketEngine")

DEFAULT_DB_PATH = "competitor_intelligence.db"


# ==============================================================================
# 1. Dynamic App Discovery
# ==============================================================================

def search_apps(query: str, n_hits: int = 12, lang: str = "en", country: str = "ps") -> List[Dict[str, Any]]:
    """
    Search Google Play Store for apps matching query keyword or category.
    Returns cleaned list of matching apps with title, developer, score, icon, and url.
    """
    if not query or not query.strip():
        return []

    query = query.strip()
    country = (country or "ps").lower()
    logger.info(f"Searching Google Play Store for: '{query}' (country: {country}, limit: {n_hits})")
    
    try: # الحماية من الانهيار 
        raw_results = search( # search دالة بحث خاصة بمكتبة google_play_scraper
            query,
            lang=lang,
            country=country,
            n_hits=n_hits
        )
    except Exception as e:
        logger.error(f"Error during Google Play search for '{query}': {e}")
        return []

    parsed_apps = []
    for item in raw_results:
        app_id = item.get("appId")
        if not app_id:
            continue
            
        score = item.get("score")
        if score is not None:
            try:
                score = round(float(score), 2)
            except (ValueError, TypeError):
                score = 0.0
        else:
            score = 0.0

        parsed_apps.append({
            "app_id": app_id,
            "title": item.get("title", "Unknown App"),
            "developer": item.get("developer", "Unknown Developer"),
            "score": score,
            "icon": item.get("icon", ""),
            "url": item.get("url", f"https://play.google.com/store/apps/details?id={app_id}"),
            "genre": item.get("genre", "General"),
            "currency": item.get("currency", "ILS"),
            "price": item.get("price", 0.0),
            "free": item.get("free", True),
        })

    logger.info(f"Found {len(parsed_apps)} apps for query '{query}'")
    return parsed_apps


# ==============================================================================
# 2. Targeted Multi-App Scraping & Cleaning
# ==============================================================================

def clean_text(text: Optional[str]) -> str:
    """
    Clean and normalize user review text:
    - Decode HTML entities
    - Remove extra white spaces and redundant line breaks
    - Normalize text encoding
    """
    if not text or not isinstance(text, str):
        return ""

    # Decode HTML entities (e.g., &amp;, &quot;)
    cleaned = html.unescape(text)
    
    # Strip HTML tags if present
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    
    # Replace multiple spaces/newlines with single space
    cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    
    return cleaned.strip()


def categorize_sentiment(score: int, text: str = "") -> str:
    """
    Categorize user feedback into sentiment based on ground-truth star rating:
    - 4 to 5 Stars -> Positive
    - 3 Stars      -> Neutral
    - 1 to 2 Stars -> Negative
    """
    try:
        rating = int(score)
    except (ValueError, TypeError):
        rating = 3 # قيمة افتراضية في حال وجود خطأ في البيانات  

    if rating >= 4:
        return "Positive"
    elif rating == 3:
        return "Neutral"
    else:
        return "Negative"


def scrape_app_reviews(
    app_id: str,
    app_title: str = "",
    count: int = 200,
    lang: str = "en",
    country: str = "PS"
) -> List[Dict[str, Any]]:
    """
    Scrapes recent customer reviews safely without memory bottlenecks.
    Enforces count bounds (typically 150 to 300 reviews).
    """
    count = max(50, min(count, 500))  # safe bounding
    country = (country or "ps").lower()
    logger.info(f"Scraping {count} reviews for app: {app_id} ('{app_title}') [Country: {country}]")

    collected_reviews: List[Dict[str, Any]] = []

    try:
        result, _ = reviews(
            app_id,
            lang=lang,
            country=country,
            sort=Sort.NEWEST,
            count=count
        )
    except Exception as e:
        logger.error(f"Failed to scrape reviews for {app_id}: {e}")
        return []

    for idx, r in enumerate(result):
        raw_content = r.get("content") or ""
        normalized_content = clean_text(raw_content)
        
        # Fallback to unique synthetic ID if reviewId is absent
        rev_id = str(r.get("reviewId") or f"{app_id}_rev_{idx}_{int(datetime.now().timestamp())}")
        score = int(r.get("score") or 0)
        sentiment = categorize_sentiment(score, normalized_content)
        
        # Timestamp formatting
        rev_date = r.get("at")
        if isinstance(rev_date, datetime):
            timestamp_str = rev_date.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_str = str(rev_date or datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        collected_reviews.append({
            "review_id": rev_id,
            "app_id": app_id,
            "app_title": app_title or app_id,
            "user_name": str(r.get("userName") or "Google User"),
            "score": score,
            "sentiment": sentiment,
            "content": raw_content,
            "clean_content": normalized_content,
            "thumbs_up_count": int(r.get("thumbsUpCount") or 0),
            "review_version": str(r.get("reviewCreatedVersion") or "Unknown"),
            "review_timestamp": timestamp_str,
        })

    logger.info(f"Successfully scraped and processed {len(collected_reviews)} reviews for {app_id}")
    return collected_reviews


def process_selected_competitors(
    selected_apps: List[Dict[str, Any]],
    reviews_per_app: int = 200,
    lang: str = "en",
    country: str = "ps"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Coordinates multi-app scraping for 2 to 4 competitors.
    Returns:
    - apps_df: DataFrame summarizing competitor metadata and sentiment breakdown
    - reviews_df: Comprehensive DataFrame of all cleaned and categorized reviews
    """
    all_reviews: List[Dict[str, Any]] = []
    apps_summary: List[Dict[str, Any]] = []

    for app in selected_apps:
        app_id = app["app_id"]
        app_title = app.get("title", app_id)
        
        scraped = scrape_app_reviews(
            app_id=app_id,
            app_title=app_title,
            count=reviews_per_app,
            lang=lang,
            country=country
        )
        all_reviews.extend(scraped)

        # Compute immediate stats for summary
        if scraped:
            temp_df = pd.DataFrame(scraped)
            total_revs = len(temp_df)
            avg_rating = round(temp_df["score"].mean(), 2)
            pos_pct = round((temp_df["sentiment"] == "Positive").sum() / total_revs * 100, 1)
            neu_pct = round((temp_df["sentiment"] == "Neutral").sum() / total_revs * 100, 1)
            neg_pct = round((temp_df["sentiment"] == "Negative").sum() / total_revs * 100, 1)
        else:
            total_revs = 0
            avg_rating = app.get("score", 0.0)
            pos_pct = neu_pct = neg_pct = 0.0

        apps_summary.append({
            "app_id": app_id,
            "title": app_title,
            "developer": app.get("developer", "Unknown"),
            "store_score": app.get("score", 0.0),
            "scraped_avg_score": avg_rating,
            "scraped_reviews_count": total_revs,
            "positive_pct": pos_pct,
            "neutral_pct": neu_pct,
            "negative_pct": neg_pct,
            "icon_url": app.get("icon", ""),
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    reviews_df = pd.DataFrame(all_reviews) if all_reviews else pd.DataFrame()
    apps_df = pd.DataFrame(apps_summary) if apps_summary else pd.DataFrame()

    return apps_df, reviews_df


# ==============================================================================
# 3. Relational Storage (SQLite Database)
# ==============================================================================

def init_db(db_path: str = DEFAULT_DB_PATH):
    """
    Initializes clean SQLite database schema for competitor intelligence storage.
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Apps table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apps (
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
        )
    """)

    # Reviews table with Foreign Key reference
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
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
        )
    """)

    # Index for fast filtering and analytics queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_app_id ON reviews(app_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_score ON reviews(score);")

    conn.commit()
    conn.close()
    logger.info(f"SQLite database schema verified/initialized at: {db_path}")


def save_to_database(
    apps_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
    db_path: str = DEFAULT_DB_PATH
):
    """
    Persists competitor apps and feedback records into SQLite database.
    Uses UPSERT / INSERT OR REPLACE logic to prevent duplicates.
    """
    if apps_df.empty and reviews_df.empty:
        logger.warning("No data provided to save to database.")
        return

    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Save apps
    if not apps_df.empty:
        for _, row in apps_df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO apps (
                    app_id, title, developer, store_score, scraped_avg_score,
                    scraped_reviews_count, positive_pct, neutral_pct, negative_pct,
                    icon_url, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row.get("app_id")),
                str(row.get("title")),
                str(row.get("developer")),
                float(row.get("store_score", 0.0)),
                float(row.get("scraped_avg_score", 0.0)),
                int(row.get("scraped_reviews_count", 0)),
                float(row.get("positive_pct", 0.0)),
                float(row.get("neutral_pct", 0.0)),
                float(row.get("negative_pct", 0.0)),
                str(row.get("icon_url", "")),
                str(row.get("last_updated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            ))

    # Save reviews
    if not reviews_df.empty:
        for _, row in reviews_df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO reviews (
                    review_id, app_id, app_title, user_name, score, sentiment,
                    content, clean_content, thumbs_up_count, review_version,
                    review_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row.get("review_id")),
                str(row.get("app_id")),
                str(row.get("app_title")),
                str(row.get("user_name")),
                int(row.get("score", 0)),
                str(row.get("sentiment")),
                str(row.get("content")),
                str(row.get("clean_content")),
                int(row.get("thumbs_up_count", 0)),
                str(row.get("review_version")),
                str(row.get("review_timestamp"))
            ))

    conn.commit()
    conn.close()
    logger.info(f"Saved {len(apps_df)} apps and {len(reviews_df)} reviews to {db_path}")


def load_from_database(db_path: str = DEFAULT_DB_PATH) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Loads saved apps and reviews from the SQLite database.
    """
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    try:
        apps_df = pd.read_sql_query("SELECT * FROM apps ORDER BY last_updated DESC", conn)
        reviews_df = pd.read_sql_query("SELECT * FROM reviews ORDER BY review_timestamp DESC", conn)
    except Exception as e:
        logger.error(f"Error loading data from database {db_path}: {e}")
        apps_df = pd.DataFrame()
        reviews_df = pd.DataFrame()
    finally:
        conn.close()

    return apps_df, reviews_df


# ==============================================================================
# 4. Automated Multi-Sheet Excel Report Generation
# ==============================================================================

def generate_excel_report(
    apps_df: pd.DataFrame,
    reviews_df: pd.DataFrame,
    file_path: Optional[str] = None
) -> bytes:
    """
    Generates an executive, styled, multi-sheet Excel workbook:
    - Sheet 1: Competitor Overview (Summary KPI comparison)
    - Sheet 2: Sentiment Matrix (Aggregated breakdown)
    - Sheet 3: Pain Points (1-2 Stars) (Filtered negative user friction)
    - Sheet 4: Full Reviews Detail (Raw & Cleaned records)
    
    Returns raw bytes for direct Streamlit download and optionally saves to disk.
    """
    wb = Workbook()
    # Remove default active sheet
    wb.remove(wb.active)

    # Styles
    navy_header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    dark_teal_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
    coral_alert_fill = PatternFill(start_color="C00000", end_color="C00000", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Calibri", size=10)
    thin_border = Border(
        left=Side(style="thin", color="D9D9D9"),
        right=Side(style="thin", color="D9D9D9"),
        top=Side(style="thin", color="D9D9D9"),
        bottom=Side(style="thin", color="D9D9D9")
    )

    def style_sheet(ws, fill_color, col_widths=None):
        for cell in ws[1]:
            cell.fill = fill_color
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
        ws.row_dimensions[1].height = 28

        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=ws.max_column):
            for cell in row:
                cell.font = data_font
                cell.border = thin_border
                if isinstance(cell.value, (int, float)):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center")

        # Auto-adjust column widths
        for col in ws.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                val = str(cell.value or "")
                if len(val) > max_len:
                    max_len = len(val)
            adjusted_width = min(max(max_len + 3, 12), 50)
            ws.column_dimensions[col_letter].width = adjusted_width

    # -------------------------------------------------------------
    # Sheet 1: Competitor Overview
    # -------------------------------------------------------------
    ws_overview = wb.create_sheet(title="Competitor Overview")
    if not apps_df.empty:
        cols_to_export = [
            "title", "developer", "store_score", "scraped_avg_score",
            "scraped_reviews_count", "positive_pct", "neutral_pct", "negative_pct", "app_id"
        ]
        available_cols = [c for c in cols_to_export if c in apps_df.columns]
        display_df = apps_df[available_cols].copy()
        display_df.rename(columns={
            "title": "App Title",
            "developer": "Developer",
            "store_score": "Store Rating",
            "scraped_avg_score": "Sample Avg Rating",
            "scraped_reviews_count": "Reviews Analyzed",
            "positive_pct": "Positive Feedback %",
            "neutral_pct": "Neutral Feedback %",
            "negative_pct": "Negative Feedback %",
            "app_id": "Application ID"
        }, inplace=True)
        
        for r in dataframe_to_rows(display_df, index=False, header=True):
            ws_overview.append(r)
    else:
        ws_overview.append(["No competitor data available"])
    style_sheet(ws_overview, navy_header_fill)

    # -------------------------------------------------------------
    # Sheet 2: Sentiment Matrix
    # -------------------------------------------------------------
    ws_matrix = wb.create_sheet(title="Sentiment Matrix")
    if not reviews_df.empty:
        matrix_df = pd.crosstab(
            reviews_df["app_title"],
            reviews_df["sentiment"],
            margins=True,
            margins_name="Total Reviews"
        ).reset_index()
        matrix_df.rename(columns={"app_title": "Competitor App"}, inplace=True)
        for r in dataframe_to_rows(matrix_df, index=False, header=True):
            ws_matrix.append(r)
    else:
        ws_matrix.append(["No sentiment matrix available"])
    style_sheet(ws_matrix, dark_teal_fill)

    # -------------------------------------------------------------
    # Sheet 3: Pain Points (1-2 Stars)
    # -------------------------------------------------------------
    ws_pain = wb.create_sheet(title="Pain Points (1-2 Stars)")
    if not reviews_df.empty and "score" in reviews_df.columns:
        pain_df = reviews_df[reviews_df["score"].isin([1, 2])].copy()
        if not pain_df.empty:
            pain_df = pain_df.sort_values(by=["thumbs_up_count", "review_timestamp"], ascending=[False, False])
            pain_cols = ["app_title", "score", "user_name", "clean_content", "thumbs_up_count", "review_timestamp"]
            pain_display = pain_df[pain_cols].copy()
            pain_display.rename(columns={
                "app_title": "Competitor App",
                "score": "Star Rating",
                "user_name": "Reviewer",
                "clean_content": "User Complaint / Feedback",
                "thumbs_up_count": "Helpful Votes (Thumbs Up)",
                "review_timestamp": "Timestamp"
            }, inplace=True)
            for r in dataframe_to_rows(pain_display, index=False, header=True):
                ws_pain.append(r)
        else:
            ws_pain.append(["No 1-star or 2-star reviews found"])
    else:
        ws_pain.append(["No review data available"])
    style_sheet(ws_pain, coral_alert_fill)

    # -------------------------------------------------------------
    # Sheet 4: Full Reviews Detail
    # -------------------------------------------------------------
    ws_full = wb.create_sheet(title="All Reviews Detail")
    if not reviews_df.empty:
        detail_cols = ["app_title", "score", "sentiment", "clean_content", "thumbs_up_count", "review_version", "review_timestamp"]
        available_detail = [c for c in detail_cols if c in reviews_df.columns]
        full_display = reviews_df[available_detail].copy()
        full_display.rename(columns={
            "app_title": "Competitor App",
            "score": "Stars",
            "sentiment": "Sentiment",
            "clean_content": "Cleaned Feedback",
            "thumbs_up_count": "Upvotes",
            "review_version": "App Version",
            "review_timestamp": "Date"
        }, inplace=True)
        for r in dataframe_to_rows(full_display, index=False, header=True):
            ws_full.append(r)
    else:
        ws_full.append(["No reviews detail available"])
    style_sheet(ws_full, dark_teal_fill)

    # Save to memory buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    data_bytes = buffer.getvalue()

    if file_path:
        with open(file_path, "wb") as f:
            f.write(data_bytes)
        logger.info(f"Excel report saved to file: {file_path}")

    return data_bytes
