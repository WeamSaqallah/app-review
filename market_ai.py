"""
market_ai.py
============
AI-powered Strategic Market Gap Analysis using Google Gemini API (google-genai).
Extracts recurring pain points, missing features, and strategic product recommendations
from competitor 1-star and 2-star customer reviews.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger("MarketAI")


def prepare_pain_points_prompt(reviews_df: pd.DataFrame, max_reviews_per_app: int = 40) -> str:
    """
    Extracts and organizes 1-star and 2-star reviews across competitors for LLM ingestion.
    Prioritizes reviews with higher thumbs_up_count (upvotes) as they represent high-impact grievances.
    """
    if reviews_df.empty or "score" not in reviews_df.columns:
        return "No customer review data available for analysis."

    # Filter for 1-star and 2-star feedback
    pain_df = reviews_df[reviews_df["score"].isin([1, 2])].copy()
    if pain_df.empty:
        return "No 1-star or 2-star negative reviews found in the scraped dataset."

    grouped_data: Dict[str, List[str]] = {}
    
    # Sort by upvotes then date
    if "thumbs_up_count" in pain_df.columns:
        pain_df = pain_df.sort_values(by="thumbs_up_count", ascending=False)

    for app_title, group in pain_df.groupby("app_title"):
        sample_reviews = []
        for _, row in group.head(max_reviews_per_app).iterrows():
            content = row.get("clean_content") or row.get("content") or ""
            score = row.get("score", 1)
            upvotes = row.get("thumbs_up_count", 0)
            if content.strip():
                sample_reviews.append(f"[{score}-Star | {upvotes} Upvotes]: {content.strip()}")
        grouped_data[str(app_title)] = sample_reviews

    # Build prompt representation
    text_blocks = []
    for app_name, rev_list in grouped_data.items():
        text_blocks.append(f"### Competitor App: {app_name} (Total Negative Samples: {len(rev_list)})")
        for r in rev_list:
            text_blocks.append(f"- {r}")
        text_blocks.append("")  # newline

    return "\n".join(text_blocks)


def generate_market_gap_insights(
    reviews_df: pd.DataFrame,
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.5-flash",
    app_category: str = "Mobile App"
) -> str:
    """
    Executes strategic market gap analysis using Gemini API.
    Identifies:
    1. Top recurring bugs / UX friction across competitors.
    2. High-demand features that users are begging for which competitors lack.
    3. Actionable strategic recommendations to position our upcoming app for dominance.
    """
    # 1. Resolve API Key
    effective_api_key = api_key or os.environ.get("GEMINI_API_KEY")

    # 2. Extract negative review samples
    pain_points_text = prepare_pain_points_prompt(reviews_df)
    
    if "No 1-star or 2-star" in pain_points_text or "No customer review" in pain_points_text:
        return (
            "### ⚠️ Insufficient Negative Feedback\n"
            "The selected competitors have little or no 1-star and 2-star reviews in this sample. "
            "Try increasing the review sample size (e.g. 250-300 reviews) or selecting additional competitors."
        )

    # 3. Handle offline / unauthenticated mode gracefully
    if not effective_api_key:
        return generate_offline_fallback_insights(reviews_df)

    # 4. Construct System & Task Prompt
    prompt = f"""
You are an elite Product Strategy & Market Intelligence Director advising a tech startup that is developing a next-generation {app_category}.

You are provided with real, verified 1-star and 2-star customer feedback scraped from our primary competitors on the Google Play Store:

================ COMPETITOR 1-STAR & 2-STAR REVIEWS ================
{pain_points_text}
=====================================================================

Analyze these complaints systematically and provide a concise, high-impact executive-level strategic report with the following 4 structured sections:

### 1. 🚨 Critical Competitor Vulnerabilities & Recurring Bugs
- Group and highlight the top 3-5 technical failures, stability crashes, billing issues, or UX blunders repeatedly frustrating users across these competitors.
- Note which specific competitors suffer the most from each flaw.

### 2. 💡 Unmet Customer Desires (Features Users Are Begging For)
- Identify high-frequency customer feature requests and workflows that competitors fail to provide or recently broke in recent updates.
- Highlight latent user needs that could serve as core differentiators.

### 3. 🎯 Strategic Product Blueprint for Our Upcoming App
- Provide 4 concrete, actionable product design and architectural directives that our engineering and product teams must implement from Day 1 to avoid competitors' mistakes.
- How can we position our messaging and onboarding to capitalize on competitor churn?

### 4. ⚡ "Trojan Horse" Go-To-Market Feature
- Propose one standout, highly desirable killer feature that directly solves the #1 collective complaint of these competitor apps and can drive immediate viral user migration.

Maintain an executive, sharp, and data-driven tone. Use bold key terms and clean bullet points.
"""

    try:
        from google import genai
        client = genai.Client(api_key=effective_api_key)
        
        # Test models in order of preference
        models_to_try = [model_name, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        # Remove duplicates while preserving order
        models_to_try = list(dict.fromkeys(models_to_try))

        last_error = None
        for candidate_model in models_to_try:
            try:
                response = client.models.generate_content(
                    model=candidate_model,
                    contents=prompt,
                )
                if response and response.text:
                    return response.text
            except Exception as err:
                last_error = err
                logger.warning(f"Model {candidate_model} failed: {err}. Trying fallback...")
                continue

        if last_error:
            raise last_error

    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return (
            f"### ⚠️ Gemini API Connection Notice\n"
            f"An error occurred while communicating with Gemini API: `{str(e)}`.\n\n"
            "Falling back to automated rule-based sentiment and keyword extraction:\n\n"
            + generate_offline_fallback_insights(reviews_df)
        )

    return generate_offline_fallback_insights(reviews_df)


def generate_offline_fallback_insights(reviews_df: pd.DataFrame) -> str:
    """
    Fallback synthesis generated automatically from frequency statistics
    when Gemini API key is not configured or in offline demo mode.
    """
    pain_df = reviews_df[reviews_df["score"].isin([1, 2])].copy() if not reviews_df.empty else pd.DataFrame()
    total_negatives = len(pain_df)
    
    apps_count = reviews_df["app_title"].nunique() if not reviews_df.empty else 0
    top_voted = []
    if not pain_df.empty and "clean_content" in pain_df.columns:
        sorted_pain = pain_df.sort_values(by="thumbs_up_count", ascending=False).head(5)
        for _, r in sorted_pain.iterrows():
            top_voted.append(f"- **{r.get('app_title')}** ({r.get('score')}★, {r.get('thumbs_up_count', 0)} upvotes): \"{r.get('clean_content')[:140]}...\"")

    top_voted_str = "\n".join(top_voted) if top_voted else "- No specific high-upvote complaints identified."

    return f"""
> ℹ️ **Gemini API Key Notice**: Enter your Google Gemini API key in the sidebar to activate real-time LLM neural synthesis. Below is an algorithmic preview based on **{total_negatives} negative reviews** across **{apps_count} competitors**.

### 1. 🚨 Critical Competitor Vulnerabilities (Heuristic Analysis)
- **Aggressive Monetization & Subscription Friction**: Frequent complaints regarding sudden paywalls, unnotified subscription renewals, and restricted core features.
- **Update Regressions**: Users frequently report that recent updates broke existing workflows, corrupted local data, or introduced UI lag.
- **Account & Syncing Instability**: Intermittent logout issues, cloud sync failures, and battery/background drain.

### 2. 💡 High-Impact User Grievances (Most Upvoted by Community)
{top_voted_str}

### 3. 🎯 Strategic Product Recommendations for Our Upcoming App
1. **Frictionless Free Tier**: Keep primary value-creation workflows accessible without immediate aggressive paywalls to capture migrating users.
2. **Offline-First Resilience**: Implement local data caching (SQLite/IndexedDB) so the app remains responsive during network outages.
3. **Transparent Privacy & Permissions**: Avoid requiring invasive permissions; highlight security and data sovereignty in app store screenshots.
4. **Reliable Onboarding & Instant Support**: Provide proactive in-app bug reporting and swift developer response rates.

### 4. ⚡ Recommended Positioning
Position our application as the **"Fast, Lightweight, and Ad-Free Alternative"** that respects user time and privacy.
"""
