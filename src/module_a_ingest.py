# -*- coding: utf-8 -*-
"""
Multilingual news ingestion module (Module A).
Supports GDELT, RSS, and Twitter (via tweepy) with language detection.
"""
import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta

import requests
from langdetect import detect

logger = logging.getLogger(__name__)

# Configuration – pulled from extra_config
from .extra_config import SUPPORTED_LANGUAGES


def _fetch_gdelt(max_records: int = 8) -> List[Dict]:
    """Fetch recent GDELT records (JSON) limited by max_records."""
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": "semiconductor OR \"chip shortage\" OR \"supply chain\" OR gallium OR TSMC",
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(max_records),
        "timespan": "24h",
        "sort": "datedesc"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CounterVerse/2.0",
        "Accept": "application/json"
    }
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=6.0)
        resp.raise_for_status()
        data = resp.json()
        articles = data.get("articles", [])
        return [{"title": a.get("title", ""), "url": a.get("url", ""), "source": a.get("domain", "GDELT Live")} for a in articles if a.get("title")]
    except Exception as e:
        logger.warning(f"GDELT fetch failed: {e}")
        return []


def _fetch_rss() -> List[Dict]:
    """Fetch headlines from a list of RSS feeds defined in .env or default Google News RSS."""
    raw_env_feeds = os.getenv("COUNTERVERSE_RSS_FEEDS", "").strip()
    feeds = [f.strip() for f in raw_env_feeds.split(",") if f.strip()]
    if not feeds:
        feeds = [
            "https://news.google.com/rss/search?q=semiconductor+chip+shortage+automotive&hl=en-IN&gl=IN&ceid=IN:en",
            "https://news.google.com/rss/search?q=supply+chain+disruption+port+automotive&hl=en-IN&gl=IN&ceid=IN:en",
        ]
    headlines = []
    for feed in feeds:
        try:
            import feedparser
            parsed = feedparser.parse(feed)
            for entry in parsed.entries[:5]:
                headlines.append({"title": entry.title, "link": getattr(entry, "link", "")})
        except Exception as e:
            logger.warning(f"RSS fetch error for {feed}: {e}")
    return headlines


def _fetch_twitter() -> Dict[str, Any]:
    """Fetch recent tweets using Tweepy (if credentials provided).

    Returns:
        dict: {"status": "not_configured" | "active" | "error", "articles": List[Dict], "message": str}
    """
    bearer_token = os.getenv("COUNTERVERSE_TWITTER_BEARER_TOKEN")
    if not bearer_token:
        return {
            "status": "not_configured",
            "message": "Twitter credentials not configured (COUNTERVERSE_TWITTER_BEARER_TOKEN missing)",
            "articles": [],
        }
    try:
        import tweepy
        client = tweepy.Client(bearer_token=bearer_token)
        tweets = client.search_recent_tweets(query="supply chain OR semiconductor", max_results=20)
        articles = [
            {
                "title": t.text,
                "url": f"https://twitter.com/i/web/status/{t.id}",
                "domain": "twitter.com",
                "source": "Twitter API v2",
                "provenance_type": "live_twitter_feed",
                "is_illustrative": False,
            }
            for t in (tweets.data or [])
        ]
        return {
            "status": "active",
            "message": f"Fetched {len(articles)} live tweets",
            "articles": articles,
        }
    except Exception as e:
        logger.warning(f"Twitter fetch failed: {e}")
        return {
            "status": "error",
            "message": f"Twitter fetch error: {str(e)}",
            "articles": [],
        }


def _filter_by_language(items: List[Dict]) -> List[Dict]:
    """Retain only items whose detected language is in SUPPORTED_LANGUAGES."""
    filtered = []
    for item in items:
        text = item.get("title") or item.get("text") or ""
        try:
            lang = detect(text)
        except Exception:
            lang = "unknown"
        if lang in SUPPORTED_LANGUAGES:
            item["lang"] = lang
            filtered.append(item)
    return filtered


def get_latest_headlines(max_records: int = 8) -> List[Dict]:
    """Aggregate headlines from all sources, filter by language, and deduplicate."""
    raw = []
    raw.extend(_fetch_gdelt(max_records))
    raw.extend(_fetch_rss())
    tw = _fetch_twitter()
    if isinstance(tw, dict):
        raw.extend(tw.get("articles", []))
    elif isinstance(tw, list):
        raw.extend(tw)
    filtered = _filter_by_language(raw)
    # simple deduplication by title
    seen = set()
    uniq = []
    for item in filtered:
        title = item.get("title")
        if title and title not in seen:
            seen.add(title)
            uniq.append(item)
    logger.info(f"Fetched {len(uniq)} multilingual headlines")
    return uniq


def scrape_web_disruption_news(max_total: int = 10) -> List[Dict]:
    """
    Live web scraping pipeline: scrapes Google News RSS and GDELT 2.0,
    filters by disruption markers, and returns scored headlines.
    """
    try:
        from .news_scraper import scrape_live_supply_chain_news
        res = scrape_live_supply_chain_news(max_total=max_total)
        return res.get("articles", [])
    except Exception as e:
        logger.error(f"Web scraping news failed: {e}")
        return []
