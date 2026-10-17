"""
app.py
======
Interactive Streamlit Dashboard for Market Intelligence & Competitor Scraping Tool.
Bilingual Support (Arabic 🇵🇸 / English 🇺🇸).
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
# Page Configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Market Intelligence & Competitor Scraping Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
# Sidebar Controls & Language Switcher
# ------------------------------------------------------------------------------
with st.sidebar:
    st.title("🌐 Language / اللغة")
    ui_lang = st.radio(
        "Select Language",
        options=["English", "العربية"],
        index=1,  # Default to Arabic for convenience
        horizontal=True,
        label_visibility="collapsed"
    )
    is_ar = (ui_lang == "العربية")

    st.markdown("---")
    st.subheader("⚙️ " + ("التحكم بالنظام" if is_ar else "System Control"))
    st.caption("إعدادات المتجر ونموذج الذكاء الاصطناعي" if is_ar else "Google Play Intelligence & LLM Settings")

    st.markdown("---")
    st.subheader("🤖 " + ("محرك تحليل الفجوات (Gemini)" if is_ar else "AI Market Gap Engine"))
    api_key_input = st.text_input(
        "مفتاح Gemini API Key" if is_ar else "Gemini API Key",
        value=os.environ.get("GEMINI_API_KEY", ""),
        type="password",
        help="أدخل مفتاح Google Gemini API. إذا ترك فارغاً سيتم توليد تقرير إحصائي بديل تلقائياً." if is_ar else "Enter your Google Gemini API Key. If left empty, an algorithmic statistical synthesis is generated."
    )
    if api_key_input:
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.success("المفتاح مفعل" if is_ar else "API Key Active", icon="🔑")

    gemini_model = st.selectbox(
        "إصدار الموديل" if is_ar else "LLM Model Version",
        options=["gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"],
        index=0
    )

    st.markdown("---")
    st.subheader("🎯 " + ("معايير السحب والجمع" if is_ar else "Scraping Parameters"))
    reviews_count = st.slider(
        "عدد المراجعات لكل تطبيق" if is_ar else "Reviews to Scrape per App",
        min_value=150,
        max_value=300,
        value=200,
        step=25,
        help="المطلوب في مواصفات المشروع: 150-300 مراجعة لكل تطبيق منافس." if is_ar else "Job requirement specifies 150-300 reviews per competitor app."
    )
    
    country_code = st.selectbox(
        "دولة متجر التطبيقات" if is_ar else "Store Market Country",
        options=["ps", "sa", "ae", "eg", "jo", "us", "gb", "ca", "de", "fr"],
        index=0,
        format_func=lambda x: {
            "ps": "🇵🇸 Palestine (فلسطين)",
            "sa": "🇸🇦 Saudi Arabia (السعودية)",
            "ae": "🇦🇪 United Arab Emirates (الإمارات)",
            "eg": "🇪🇬 Egypt (مصر)",
            "jo": "🇯🇴 Jordan (الأردن)",
            "us": "🇺🇸 United States",
            "gb": "🇬🇧 United Kingdom",
            "ca": "🇨🇦 Canada",
            "de": "🇩🇪 Germany",
            "fr": "🇫🇷 France"
        }.get(x, x.upper())
    )

    review_lang = st.selectbox(
        "لغة المراجعات المسحوبة" if is_ar else "Scraped Reviews Language",
        options=["ar", "en"],
        index=0 if country_code in ["ps", "sa", "ae", "eg", "jo"] else 1,
        format_func=lambda x: "🇸🇦 العربية (Arabic)" if x == "ar" else "🇺🇸 الإنجليزية (English)"
    )

    st.markdown("---")
    st.subheader("💾 " + ("فحص قاعدة البيانات" if is_ar else "Database Quick Check"))
    saved_apps, saved_revs = me.load_from_database()
    st.metric("المنافسون المحفوظون" if is_ar else "Stored Competitors", len(saved_apps))
    st.metric("المراجعات بالقاعدة" if is_ar else "Total Reviews in DB", len(saved_revs))
    if st.button("🔄 " + ("إعادة التحميل من SQLite" if is_ar else "Reload from SQLite")):
        st.session_state["apps_df"] = saved_apps
        st.session_state["reviews_df"] = saved_revs
        if not saved_apps.empty and not saved_revs.empty:
            st.session_state["excel_data"] = me.generate_excel_report(saved_apps, saved_revs)
        st.rerun()


# ------------------------------------------------------------------------------
# Modern CSS Styling with RTL Support
# ------------------------------------------------------------------------------
rtl_css = """
    body, .stMarkdown, .hero-header, .metric-card {
        direction: rtl;
        text-align: right;
    }
""" if is_ar else ""

st.markdown(f"""
<style>
    {rtl_css}
    .main {{
        background-color: #f8fafc;
    }}
    
    /* Header Gradient Banner */
    .hero-header {{
        background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0284c7 100%);
        padding: 2.2rem 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    }}
    .hero-title {{
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.025em;
    }}
    .hero-subtitle {{
        font-size: 1.05rem;
        margin-top: 0.6rem;
        color: #93c5fd;
        font-weight: 400;
    }}

    /* Metric Cards */
    .metric-card {{
        background: white;
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}
    .metric-label {{
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        color: #64748b;
        letter-spacing: 0.05em;
    }}
    .metric-val {{
        font-size: 2rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 0.25rem;
    }}
</style>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# Hero Header
# ------------------------------------------------------------------------------
hero_title_text = "أداة استخبارات السوق وتحليل المنافسين" if is_ar else "Market Intelligence & Competitor Scraping Tool"
hero_sub_text = (
    "البحث الذكي في Google Play • سحب مراجعات المنافسين بأمان • تخزين في SQLite • تحليلات Plotly • توليد استراتيجية السوق بالذكاء الاصطناعي (Gemini)"
    if is_ar else
    "Automated Google Play Store Discovery • Multi-App Review Scraping • SQLite Relational Pipeline • Plotly Analytics • AI Market Gap Synthesis"
)

st.markdown(f"""
<div class="hero-header">
    <h1 class="hero-title">{hero_title_text}</h1>
    <p class="hero-subtitle">{hero_sub_text}</p>
</div>
""", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# Step 1: Dynamic App Discovery
# ------------------------------------------------------------------------------
step1_title = "1️⃣ البحث الديناميكي عن التطبيقات" if is_ar else "1️⃣ Dynamic App Discovery"
step1_desc = (
    "ابحث عن اسم تطبيق، كلمة مفتاحية، أو مجال عمل (مثل: `food delivery`, `fitness tracker`, `توصيل`, `خدمات بنكية`):"
    if is_ar else
    "Search for an app name, niche keyword, or market category (e.g., `food delivery`, `fitness tracker`, `habit tracker`)."
)
st.markdown(f"### {step1_title}")
st.write(step1_desc)

col_search, col_btn = st.columns([5, 1])
with col_search:
    search_query = st.text_input(
        "Search Keyword",
        value="",
        placeholder="مثال: food delivery, fitness tracker, توصيل طلبات..." if is_ar else "e.g. food delivery, budget planner, habit tracker...",
        label_visibility="collapsed"
    )
with col_btn:
    search_clicked = st.button("🔍 " + ("بحث في المتجر" if is_ar else "Search Play Store"), use_container_width=True, type="primary")

if search_clicked:
    if search_query.strip():
        spinner_msg = f"جاري البحث في Google Play عن '{search_query}'..." if is_ar else f"Querying Google Play Store for '{search_query}'..."
        with st.spinner(spinner_msg):
            results = me.search_apps(search_query, n_hits=12, lang=review_lang, country=country_code)
            st.session_state["search_results"] = results
            st.session_state["search_query_term"] = search_query
            if not results:
                st.warning(f"لم يتم العثور على تطبيقات لكلمة '{search_query}'. جرب كلمة أخرى." if is_ar else f"No apps found for '{search_query}'. Try a different keyword.")
    else:
        st.error("يرجى كتابة كلمة مفتاحية للبحث." if is_ar else "Please enter a search keyword.")


# ------------------------------------------------------------------------------
# Step 2: Multi-App Selection & Targeted Scraping
# ------------------------------------------------------------------------------
if st.session_state["search_results"]:
    st.markdown("---")
    step2_title = "2️⃣ تحديد المنافسين (اختر من 2 إلى 4 تطبيقات)" if is_ar else "2️⃣ Multi-App Selection (Choose 2 to 4 Competitors)"
    step2_desc = (
        "ضع علامة صح في المربع بجانب 2 أو 3 أو 4 تطبيقات لمقارنة مراجعات عملائها:"
        if is_ar else
        "Check the boxes next to 2, 3, or 4 competing apps to compare their customer feedback."
    )
    st.markdown(f"### {step2_title}")
    st.caption(step2_desc)

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
                            dev_label = "بواسطة " if is_ar else "By "
                            st.caption(f"{dev_label}{app_info['developer'][:25]}")
                            st.write(f"⭐ **{app_info['score']}** / 5.0")

                        # Checkbox
                        chk_label = "تحديد للمقارنة" if is_ar else "Select for Scraping"
                        is_selected = st.checkbox(
                            chk_label,
                            key=f"chk_{app_info['app_id']}",
                            value=False
                        )
                        if is_selected:
                            selected_apps_temp.append(app_info)

    # Validate 2 to 4 apps selection constraint
    num_selected = len(selected_apps_temp)
    selected_badge = f"**{'المنافسون المحددون:' if is_ar else 'Selected Competitors:'}** `{num_selected}` / 4 ({'الحد الأدنى 2' if is_ar else 'Minimum 2 required'})"
    st.markdown(selected_badge)

    col_action1, col_action2 = st.columns([2, 4])
    with col_action1:
        scrape_btn_text = "🚀 " + ("تشغيل سحب وتحليل البيانات" if is_ar else "Scrape & Run Analysis Pipeline")
        scrape_btn = st.button(
            scrape_btn_text,
            type="primary",
            use_container_width=True,
            disabled=not (2 <= num_selected <= 4)
        )
    with col_action2:
        if num_selected < 2:
            st.info("💡 " + ("يرجى اختيار تطبيقين (2) على الأقل لإجراء المقارنة." if is_ar else "Please select at least 2 apps to perform comparative analysis."))
        elif num_selected > 4:
            st.error("⚠️ " + ("الحد الأقصى هو 4 تطبيقات. يرجى إلغاء تحديد التطبيقات الزائدة." if is_ar else "Maximum selection is 4 apps. Please uncheck extra applications."))
        else:
            st.success(f"✅ {'جاهز! تم تحديد' if is_ar else 'Ready!'} {num_selected} {'تطبيقات منافسة للتحليل.' if is_ar else 'competitor apps selected for targeted extraction.'}")

    if scrape_btn and (2 <= num_selected <= 4):
        st.session_state["selected_apps"] = selected_apps_temp
        
        progress_bar = st.progress(0, text="بدء تشغيل محرك السحب..." if is_ar else "Initializing scraping engine...")
        status_box = st.status("تنفيذ خط معالجة البيانات..." if is_ar else "Running Data Pipeline...", expanded=True)
        
        with status_box:
            step1_msg = f"📥 1. جاري سحب {reviews_count} مراجعة لكل تطبيق من Google Play بأمان..." if is_ar else f"📥 1. Scraping {reviews_count} reviews per competitor safely from Google Play..."
            st.write(step1_msg)
            progress_bar.progress(25, text="سحب المراجعات..." if is_ar else "Scraping customer reviews...")
            
            apps_df, reviews_df = me.process_selected_competitors(
                selected_apps=selected_apps_temp,
                reviews_per_app=reviews_count,
                lang=review_lang,
                country=country_code
            )
            
            step2_msg = f"🧹 2. تم تنظيف وتوحيد النصوص، استخراج التواريخ، وتصنيف المشاعر ({len(reviews_df)} مراجعة إجمالاً)." if is_ar else f"🧹 2. Cleaned and normalized text, parsed timestamps, and categorized sentiment ({len(reviews_df)} total records)."
            st.write(step2_msg)
            progress_bar.progress(50, text="حفظ البيانات في SQLite..." if is_ar else "Persisting to SQLite database...")

            step3_msg = "💾 3. حفظ البيانات في قاعدة SQLite `competitor_intelligence.db`..." if is_ar else "💾 3. Storing data into SQLite schema `competitor_intelligence.db`..."
            st.write(step3_msg)
            me.save_to_database(apps_df, reviews_df)
            
            step4_msg = "📑 4. إنشاء تقرير إكسل احترافي متعدد الصفحات..." if is_ar else "📑 4. Compiling automated multi-sheet Excel report..."
            st.write(step4_msg)
            progress_bar.progress(75, text="توليد تقرير الإكسل والتحليل الاستراتيجي..." if is_ar else "Generating Excel report & AI Analysis...")
            excel_bytes = me.generate_excel_report(apps_df, reviews_df, file_path="competitor_analysis_report.xlsx")
            
            step5_msg = "🤖 5. تنفيذ تحليل فجوات السوق بالذكاء الاصطناعي (Gemini)..." if is_ar else "🤖 5. Executing AI Strategic Market Gap Analysis with Google Gemini..."
            st.write(step5_msg)
            category_term = st.session_state.get("search_query_term", "Mobile Application")
            ai_insights_text = mai.generate_market_gap_insights(
                reviews_df=reviews_df,
                api_key=api_key_input or os.environ.get("GEMINI_API_KEY"),
                model_name=gemini_model,
                app_category=category_term,
                output_lang="ar" if is_ar else "en"
            )
            
            progress_bar.progress(100, text="اكتمل تنفيذ خط المعالجة بنجاح!" if is_ar else "Pipeline execution complete!")
            status_box.update(
                label="اكتمل استخراج وتحليل بيانات المنافسين بنجاح!" if is_ar else "Competitor Intelligence Pipeline Complete!",
                state="complete",
                expanded=False
            )

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
    step3_title = "3️⃣ لوحة المقارنة والتحليلات البيانية" if is_ar else "3️⃣ Competitor Comparison Dashboard"
    st.markdown(f"### {step3_title}")
    
    total_reviews_analyzed = len(reviews_df)
    total_competitors = len(apps_df)
    overall_avg_rating = round(reviews_df["score"].mean(), 2)
    overall_negative_pct = round((reviews_df["sentiment"] == "Negative").sum() / total_reviews_analyzed * 100, 1)

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{"المنافسون المحللون" if is_ar else "Competitors Analyzed"}</div>
            <div class="metric-val">{total_competitors}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{"المراجعات المسحوبة" if is_ar else "Reviews Sampled"}</div>
            <div class="metric-val">{total_reviews_analyzed}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{"متوسط التقييم" if is_ar else "Sample Avg Rating"}</div>
            <div class="metric-val">⭐ {overall_avg_rating}</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{"نسبة المراجعات السلبية" if is_ar else "Negative Feedback Ratio"}</div>
            <div class="metric-val" style="color: #ef4444;">{overall_negative_pct}%</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # Visual Charts (Plotly)
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📊 " + ("توزيع المشاعر بين المنافسين" if is_ar else "Sentiment Segmentation Across Competitors"))
        sentiment_summary = reviews_df.groupby(["app_title", "sentiment"]).size().reset_index(name="count")
        
        # Translate sentiment labels if Arabic
        if is_ar:
            sentiment_summary["sentiment_display"] = sentiment_summary["sentiment"].map({
                "Positive": "إيجابي (Positive)",
                "Neutral": "محايد (Neutral)",
                "Negative": "سلبي (Negative)"
            }).fillna(sentiment_summary["sentiment"])
            color_map = {"إيجابي (Positive)": "#22c55e", "محايد (Neutral)": "#94a3b8", "سلبي (Negative)": "#ef4444"}
            color_col = "sentiment_display"
        else:
            color_map = {"Positive": "#22c55e", "Neutral": "#94a3b8", "Negative": "#ef4444"}
            color_col = "sentiment"

        fig_sentiment = px.bar(
            sentiment_summary,
            x="app_title",
            y="count",
            color=color_col,
            barmode="group",
            color_discrete_map=color_map,
            labels={"app_title": "التطبيق" if is_ar else "Competitor App", "count": "عدد المراجعات" if is_ar else "Reviews Count", color_col: "المشاعر" if is_ar else "Sentiment"},
            template="plotly_white"
        )
        fig_sentiment.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_sentiment, use_container_width=True)

    with col_chart2:
        st.subheader("⭐ " + ("توزيع النجوم (1 إلى 5 نجوم)" if is_ar else "Star Rating Distribution (1 to 5 Stars)"))
        rating_summary = reviews_df.groupby(["app_title", "score"]).size().reset_index(name="count")
        rating_suffix = " نجوم" if is_ar else " Star"
        rating_summary["score"] = rating_summary["score"].astype(str) + rating_suffix
        
        fig_rating = px.bar(
            rating_summary,
            x="app_title",
            y="count",
            color="score",
            barmode="stack",
            color_discrete_sequence=["#ef4444", "#f97316", "#eab308", "#84cc16", "#10b981"],
            labels={"app_title": "التطبيق" if is_ar else "Competitor App", "count": "عدد المراجعات" if is_ar else "Reviews Count", "score": "التقييم" if is_ar else "Rating"},
            template="plotly_white"
        )
        fig_rating.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_rating, use_container_width=True)

    # Pain Points Grievance Scatter (Upvotes vs Score)
    st.subheader("🔥 " + ("نقاط الألم الأكثر تأثيراً (التصويتات vs النجوم)" if is_ar else "High-Impact Friction Points (Helpful Votes vs Star Rating)"))
    fig_scatter = px.scatter(
        reviews_df[reviews_df["score"].isin([1, 2])],
        x="review_timestamp",
        y="thumbs_up_count",
        color="app_title",
        size="thumbs_up_count",
        size_max=25,
        hover_data=["clean_content", "score", "user_name"],
        labels={
            "review_timestamp": "تاريخ المراجعة" if is_ar else "Review Date",
            "thumbs_up_count": "عدد التأييدات (Upvotes)" if is_ar else "Upvotes (Helpful Count)",
            "app_title": "التطبيق" if is_ar else "App"
        },
        template="plotly_white"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # --------------------------------------------------------------------------
    # Step 4: AI Strategic Market Gap Analysis
    # --------------------------------------------------------------------------
    st.markdown("---")
    step4_title = "4️⃣ تحليل فجوات السوق بالذكاء الاصطناعي (AI-Powered)" if is_ar else "4️⃣ Strategic Market Gap Analysis (AI-Powered)"
    st.markdown(f"### {step4_title}")
    
    if st.session_state["ai_insights"]:
        with st.container(border=True):
            st.markdown(st.session_state["ai_insights"])
            
            c_reai, _ = st.columns([2, 5])
            with c_reai:
                reai_text = "🔄 " + ("إعادة توليد التحليل بالذكاء الاصطناعي" if is_ar else "Re-run AI Gap Analysis")
                if st.button(reai_text, use_container_width=True):
                    with st.spinner("جاري توليد تقرير استراتيجي جديد..." if is_ar else "Generating fresh AI Strategic Audit..."):
                        insights = mai.generate_market_gap_insights(
                            reviews_df=reviews_df,
                            api_key=api_key_input or os.environ.get("GEMINI_API_KEY"),
                            model_name=gemini_model,
                            app_category=st.session_state.get("search_query_term", "Mobile Application"),
                            output_lang="ar" if is_ar else "en"
                        )
                        st.session_state["ai_insights"] = insights
                        st.rerun()

    # --------------------------------------------------------------------------
    # Step 5: Relational Explorer & Multi-Sheet Excel Download
    # --------------------------------------------------------------------------
    st.markdown("---")
    step5_title = "5️⃣ التقارير ومستكشف البيانات" if is_ar else "5️⃣ Reports & Relational Data Explorer"
    st.markdown(f"### {step5_title}")
    
    col_dl1, col_dl2 = st.columns([2, 4])
    with col_dl1:
        if st.session_state["excel_data"] is not None:
            now_str = datetime.now().strftime("%Y%m%d_%H%M")
            dl_btn_label = "📥 " + ("تحميل تقرير إكسل متعدد الصفحات (.xlsx)" if is_ar else "Download Multi-Sheet Excel Report (.xlsx)")
            st.download_button(
                label=dl_btn_label,
                data=st.session_state["excel_data"],
                file_name=f"Competitor_Intelligence_Report_{now_str}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        else:
            if st.button("توليد تقرير الإكسل الآن" if is_ar else "Generate Excel Report Now"):
                excel_bytes = me.generate_excel_report(apps_df, reviews_df)
                st.session_state["excel_data"] = excel_bytes
                st.rerun()

    with col_dl2:
        st.caption(
            "يتضمن 4 صفحات منسقة: **نظرة عامة على المنافسين**، **مصفوفة المشاعر**، **نقاط الألم (1-2 نجوم)**، و**جميع المراجعات المنظفة**."
            if is_ar else
            "Includes: **Competitor Overview**, **Sentiment Matrix**, **Pain Points (1-2 Stars)**, and **All Reviews Detail** sheets."
        )

    # Tabs for Data Inspection
    tab1_label = "📋 ملخص المنافسين" if is_ar else "📋 Competitor Summary"
    tab2_label = "🛑 نقاط الألم (1-2 نجوم)" if is_ar else "🛑 1-2 Star Pain Points"
    tab3_label = "📝 جميع المراجعات" if is_ar else "📝 All Reviews Dataset"
    tab4_label = "🗄️ سجلات SQLite" if is_ar else "🗄️ SQLite Database Records"

    tab_overview, tab_pain, tab_raw, tab_db = st.tabs([tab1_label, tab2_label, tab3_label, tab4_label])

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
        f_app = st.multiselect(
            "تصفية بحسب التطبيق" if is_ar else "Filter by App",
            options=list(reviews_df["app_title"].unique()),
            default=list(reviews_df["app_title"].unique())
        )
        f_sent = st.multiselect(
            "تصفية بحسب المشاعر" if is_ar else "Filter by Sentiment",
            options=["Positive", "Neutral", "Negative"],
            default=["Positive", "Neutral", "Negative"]
        )
        
        filtered_df = reviews_df[
            (reviews_df["app_title"].isin(f_app)) &
            (reviews_df["sentiment"].isin(f_sent))
        ]
        st.dataframe(filtered_df, use_container_width=True)

    with tab_db:
        st.write("البيانات المحفوظة حالياً في `competitor_intelligence.db`:" if is_ar else "Data actively saved in `competitor_intelligence.db`:")
        db_apps, db_revs = me.load_from_database()
        st.write(f"**{'جدول التطبيقات' if is_ar else 'Apps Table'} (`apps`):** {len(db_apps)} records")
        st.dataframe(db_apps, use_container_width=True)
        st.write(f"**{'جدول المراجعات' if is_ar else 'Reviews Table'} (`reviews`):** {len(db_revs)} records")
        st.dataframe(db_revs.head(100), use_container_width=True)
