"""
app.py
======
Interactive Streamlit Dashboard for Market Intelligence & Competitor Scraping Tool.
Enables dynamic app discovery, multi-app selection (2 to 4 competitors), targeted scraping,
relational persistence (SQLite), interactive Plotly visualization, multi-sheet Excel export,
and AI-powered market gap insights via Google Gemini.
"""

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

import market_engine as me
import market_ai as mai

# ------------------------------------------------------------------------------
# Page Configuration & Custom CSS
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Market Intelligence & Competitor Scraping Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom modern CSS styling
st.markdown("""
<style>
    /* Global Styles */
    .main {
        background-color: #f8fafc;
    }
    
    /* Header Gradient Banner */
    .hero-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0284c7 100%);
        padding: 2.2rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    }
    .hero-title {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.025em;
    }
    .hero-subtitle {
        font-size: 1.05rem;
        margin-top: 0.6rem;
        color: #93c5fd;
        font-weight: 400;
    }

    /* Cards */
    .metric-card {
        background: white;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.05em;
    }
    .metric-val {
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 0.25rem;
    }

    /* App Selection Card */
    .app-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    
    /* Badges */
    .badge-primary {
        background-color: #dbeafe;
        color: #1d4ed8;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-success {
        background-color: #dcfce7;
        color: #15803d;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-danger {
        background-color: #fee2e2;
        color: #b91c1c;
        padding: 0.2rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# Session State Initialization
# ------------------------------------------------------------------------------
if "search_results" not in st.session_state:
    st.session_state["search_results"] = []
if "selected_apps" not in st.session_state:
    st.session_state["selected_apps"] = []
if "apps_df" not in st.session_state:
    st.session_state["apps_df"] = pd.DataFrame()
if "reviews_df" not in st.session_state:
    st.session_state["reviews_df"] = pd.DataFrame()
if "ai_insights" not in st.session_state:
    st.session_state["ai_insights"] = ""
if "excel_data" not in st.session_state:
    st.session_state["excel_data"] = None


# ------------------------------------------------------------------------------
# Sidebar Controls
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ System Control")
    st.caption("Google Play Intelligence & LLM Settings")

    st.markdown("---")
    st.subheader("🤖 AI Market Gap Engine")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=os.environ.get("GEMINI_API_KEY", ""),
        type="password",
        help="Enter your Google Gemini API Key. If left empty, an algorithmic statistical synthesis is generated."
    )
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.success("API Key Active", icon="🔑")

    gemini_model = st.selectbox(
        "LLM Model Version",
        options=["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
        index=0
    )

    st.markdown("---")
    st.subheader("🎯 Scraping Parameters")
    reviews_count = st.slider(
        "Reviews to Scrape per App",
        min_value=150,
        max_value=300,
        value=200,
        step=25,
        help="Job requirement specifies 150-300 reviews per competitor app."
    )
    
    country_code = st.selectbox(
        "Store Market Country",
        options=["us", "gb", "ca", "de", "fr", "ae", "sa"],
        index=0,
        format_func=lambda x: {
            "us": "🇺🇸 United States",
            "gb": "🇬🇧 United Kingdom",
            "ca": "🇨🇦 Canada",
            "de": "🇩🇪 Germany",
            "fr": "🇫🇷 France",
            "ae": "🇦🇪 United Arab Emirates",
            "sa": "🇸🇦 Saudi Arabia"
        }.get(x, x.upper())
    )

    st.markdown("---")
    st.subheader("💾 Database Quick Check")
    saved_apps, saved_revs = me.load_from_database()
    st.metric("Stored Competitors", len(saved_apps))
    st.metric("Total Reviews in DB", len(saved_revs))
    if st.button("🔄 Reload from SQLite"):
        st.session_state["apps_df"] = saved_apps
        st.session_state["reviews_df"] = saved_revs
        if not saved_apps.empty and not saved_revs.empty:
            st.session_state["excel_data"] = me.generate_excel_report(saved_apps, saved_revs)
        st.rerun()


# ------------------------------------------------------------------------------
# Hero Header
# ------------------------------------------------------------------------------
st.markdown("""
<div class="hero-header">
    <h1 class="hero-title">Market Intelligence & Competitor Scraping Tool</h1>
    <p class="hero-subtitle">
        Automated Google Play Store Discovery • Multi-App Review Scraping • SQLite Relational Pipeline • Plotly Analytics • AI Market Gap Synthesis
    </p>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# Step 1: Dynamic App Discovery
# ------------------------------------------------------------------------------
st.markdown("### 1️⃣ Dynamic App Discovery")
st.write("Search for an app name, niche keyword, or market category (e.g., `food delivery`, `fitness tracker`, `habit tracker`).")

col_search, col_btn = st.columns([5, 1])
with col_search:
    search_query = st.text_input(
        "Search Keyword",
        value="",
        placeholder="e.g. food delivery, budget planner, habit tracker...",
        label_visibility="collapsed"
    )
with col_btn:
    search_clicked = st.button("🔍 Search Play Store", use_container_width=True, type="primary")

if search_clicked:
    if search_query.strip():
        with st.spinner(f"Querying Google Play Store for '{search_query}'..."):
            results = me.search_apps(search_query, n_hits=12, country=country_code)
            st.session_state["search_results"] = results
            st.session_state["search_query_term"] = search_query
            if not results:
                st.warning(f"No apps found for '{search_query}'. Try a different keyword.")
    else:
        st.error("Please enter a search keyword.")


# ------------------------------------------------------------------------------
# Step 2: Multi-App Selection & Targeted Scraping
# ------------------------------------------------------------------------------
if st.session_state["search_results"]:
    st.markdown("---")
    st.markdown("### 2️⃣ Multi-App Selection (Choose 2 to 4 Competitors)")
    st.caption("Check the boxes next to 2, 3, or 4 competing apps to compare their customer feedback.")

    # Grid of apps with Checkboxes
    raw_results = st.session_state["search_results"]
    cols_per_row = 3
    selected_apps_temp = []

    for i in range(0, len(raw_results), cols_per_row):
        row_cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(raw_results):
                app_info = raw_results[idx]
                with row_cols[j]:
                    with st.container(border=True):
                        c_img, c_meta = st.columns([1, 3])
                        with c_img:
                            if app_info.get("icon"):
                                st.image(app_info["icon"], width=65)
                            else:
                                st.write("📱")
                        with c_meta:
                            st.markdown(f"**{app_info['title'][:28]}**")
                            st.caption(f"By {app_info['developer'][:25]}")
                            st.write(f"⭐ **{app_info['score']}** / 5.0")

                        # Checkbox for selection
                        is_selected = st.checkbox(
                            f"Select for Scraping",
                            key=f"chk_{app_info['app_id']}",
                            value=False
                        )
                        if is_selected:
                            selected_apps_temp.append(app_info)

    # Validate 2 to 4 apps selection constraint
    num_selected = len(selected_apps_temp)
    st.markdown(f"**Selected Competitors:** `{num_selected}` / 4 (Minimum 2 required)")

    col_action1, col_action2 = st.columns([2, 4])
    with col_action1:
        scrape_btn = st.button(
            "🚀 Scrape & Run Analysis Pipeline",
            type="primary",
            use_container_width=True,
            disabled=not (2 <= num_selected <= 4)
        )
    with col_action2:
        if num_selected < 2:
            st.info("💡 Please select at least **2 apps** to perform comparative analysis.")
        elif num_selected > 4:
            st.error("⚠️ Maximum selection is **4 apps**. Please uncheck extra applications.")
        else:
            st.success(f"✅ Ready! {num_selected} competitor apps selected for targeted extraction.")

    if scrape_btn and (2 <= num_selected <= 4):
        st.session_state["selected_apps"] = selected_apps_temp
        
        progress_bar = st.progress(0, text="Initializing scraping engine...")
        status_box = st.status("Running Data Pipeline...", expanded=True)
        
        with status_box:
            st.write(f"📥 1. Scraping {reviews_count} reviews per competitor safely from Google Play...")
            progress_bar.progress(25, text="Scraping customer reviews...")
            
            apps_df, reviews_df = me.process_selected_competitors(
                selected_apps=selected_apps_temp,
                reviews_per_app=reviews_count,
                lang="en",
                country=country_code
            )
            
            st.write(f"🧹 2. Cleaned and normalized text, parsed timestamps, and categorized sentiment ({len(reviews_df)} total records).")
            progress_bar.progress(50, text="Persisting to SQLite database...")

            st.write("💾 3. Storing data into SQLite schema `competitor_intelligence.db`...")
            me.save_to_database(apps_df, reviews_df)
            
            st.write("📑 4. Compiling automated multi-sheet Excel report...")
            progress_bar.progress(75, text="Generating Excel report & AI Analysis...")
            excel_bytes = me.generate_excel_report(apps_df, reviews_df, file_path="competitor_analysis_report.xlsx")
            
            st.write("🤖 5. Executing AI Strategic Market Gap Analysis with Google Gemini...")
            category_term = st.session_state.get("search_query_term", "Mobile Application")
            ai_insights_text = mai.generate_market_gap_insights(
                reviews_df=reviews_df,
                api_key=api_key_input or os.environ.get("GEMINI_API_KEY"),
                model_name=gemini_model,
                app_category=category_term
            )
            
            progress_bar.progress(100, text="Pipeline execution complete!")
            status_box.update(label="Competitor Intelligence Pipeline Complete!", state="complete", expanded=False)

        # Store in session state
        st.session_state["apps_df"] = apps_df
        st.session_state["reviews_df"] = reviews_df
        st.session_state["excel_data"] = excel_bytes
        st.session_state["ai_insights"] = ai_insights_text
        st.rerun()


# ------------------------------------------------------------------------------
# Step 3, 4, 5: Visualizations, AI Insights, & Data Export
# ------------------------------------------------------------------------------
apps_df = st.session_state["apps_df"]
reviews_df = st.session_state["reviews_df"]

if not apps_df.empty and not reviews_df.empty:
    st.markdown("---")
    
    # KPI Metrics Header
    st.markdown("### 3️⃣ Competitor Comparison Dashboard")
    
    total_reviews_analyzed = len(reviews_df)
    total_competitors = len(apps_df)
    overall_avg_rating = round(reviews_df["score"].mean(), 2)
    overall_negative_pct = round((reviews_df["sentiment"] == "Negative").sum() / total_reviews_analyzed * 100, 1)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Competitors Analyzed</div>
            <div class="metric-val">{total_competitors}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Reviews Sampled</div>
            <div class="metric-val">{total_reviews_analyzed}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Sample Avg Rating</div>
            <div class="metric-val">⭐ {overall_avg_rating}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Negative Feedback Ratio</div>
            <div class="metric-val" style="color: #ef4444;">{overall_negative_pct}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Visual Charts (Plotly)
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📊 Sentiment Segmentation Across Competitors")
        sentiment_summary = reviews_df.groupby(["app_title", "sentiment"]).size().reset_index(name="count")
        
        fig_sentiment = px.bar(
            sentiment_summary,
            x="app_title",
            y="count",
            color="sentiment",
            barmode="group",
            color_discrete_map={"Positive": "#22c55e", "Neutral": "#94a3b8", "Negative": "#ef4444"},
            labels={"app_title": "Competitor App", "count": "Reviews Count", "sentiment": "Sentiment"},
            template="plotly_white"
        )
        fig_sentiment.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_sentiment, use_container_width=True)

    with col_chart2:
        st.subheader("⭐ Star Rating Distribution (1 to 5 Stars)")
        rating_summary = reviews_df.groupby(["app_title", "score"]).size().reset_index(name="count")
        rating_summary["score"] = rating_summary["score"].astype(str) + " Star"
        
        fig_rating = px.bar(
            rating_summary,
            x="app_title",
            y="count",
            color="score",
            barmode="stack",
            color_discrete_sequence=["#ef4444", "#f97316", "#eab308", "#84cc16", "#10b981"],
            labels={"app_title": "Competitor App", "count": "Reviews Count", "score": "Rating"},
            template="plotly_white"
        )
        fig_rating.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_rating, use_container_width=True)

    # Pain Points Grievance Scatter (Upvotes vs Score)
    st.subheader("🔥 High-Impact Friction Points (Helpful Votes vs Star Rating)")
    fig_scatter = px.scatter(
        reviews_df[reviews_df["score"].isin([1, 2])],
        x="review_timestamp",
        y="thumbs_up_count",
        color="app_title",
        size="thumbs_up_count",
        size_max=25,
        hover_data=["clean_content", "score", "user_name"],
        labels={"review_timestamp": "Review Date", "thumbs_up_count": "Upvotes (Helpful Count)", "app_title": "App"},
        template="plotly_white"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # --------------------------------------------------------------------------
    # Step 4: AI Strategic Market Gap Analysis
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 4️⃣ Strategic Market Gap Analysis (AI-Powered)")
    
    if st.session_state["ai_insights"]:
        with st.container(border=True):
            st.markdown(st.session_state["ai_insights"])
            
            c_reai, _ = st.columns([2, 5])
            with c_reai:
                if st.button("🔄 Re-run AI Gap Analysis", use_container_width=True):
                    with st.spinner("Generating fresh AI Strategic Audit..."):
                        insights = mai.generate_market_gap_insights(
                            reviews_df=reviews_df,
                            api_key=api_key_input or os.environ.get("GEMINI_API_KEY"),
                            model_name=gemini_model,
                            app_category=st.session_state.get("search_query_term", "Mobile Application")
                        )
                        st.session_state["ai_insights"] = insights
                        st.rerun()

    # --------------------------------------------------------------------------
    # Step 5: Relational Explorer & Multi-Sheet Excel Download
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### 5️⃣ Reports & Relational Data Explorer")
    
    col_dl1, col_dl2 = st.columns([2, 4])
    with col_dl1:
        if st.session_state["excel_data"] is not None:
            now_str = datetime.now().strftime("%Y%m%d_%H%M")
            st.download_button(
                label="📥 Download Multi-Sheet Excel Report (.xlsx)",
                data=st.session_state["excel_data"],
                file_name=f"Competitor_Intelligence_Report_{now_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        else:
            if st.button("Generate Excel Report Now"):
                excel_bytes = me.generate_excel_report(apps_df, reviews_df)
                st.session_state["excel_data"] = excel_bytes
                st.rerun()

    with col_dl2:
        st.caption("Includes: **Competitor Overview**, **Sentiment Matrix**, **Pain Points (1-2 Stars)**, and **All Reviews Detail** sheets.")

    # Tabs for Data Inspection
    tab_overview, tab_pain, tab_raw, tab_db = st.tabs([
        "📋 Competitor Summary",
        "🛑 1-2 Star Pain Points",
        "📝 All Reviews Dataset",
        "🗄️ SQLite Database Records"
    ])

    with tab_overview:
        st.dataframe(apps_df, use_container_width=True)

    with tab_pain:
        pain_df = reviews_df[reviews_df["score"].isin([1, 2])]
        st.dataframe(
            pain_df[["app_title", "score", "thumbs_up_count", "clean_content", "review_timestamp"]],
            use_container_width=True
        )

    with tab_raw:
        # Filter controls
        f_app = st.multiselect("Filter by App", options=list(reviews_df["app_title"].unique()), default=list(reviews_df["app_title"].unique()))
        f_sent = st.multiselect("Filter by Sentiment", options=["Positive", "Neutral", "Negative"], default=["Positive", "Neutral", "Negative"])
        
        filtered_df = reviews_df[
            (reviews_df["app_title"].isin(f_app)) &
            (reviews_df["sentiment"].isin(f_sent))
        ]
        st.dataframe(filtered_df, use_container_width=True)

    with tab_db:
        st.write("Data actively saved in `competitor_intelligence.db`:")
        db_apps, db_revs = me.load_from_database()
        st.write(f"**Apps Table (`apps`):** {len(db_apps)} records")
        st.dataframe(db_apps, use_container_width=True)
        st.write(f"**Reviews Table (`reviews`):** {len(db_revs)} records")
        st.dataframe(db_revs.head(100), use_container_width=True)
