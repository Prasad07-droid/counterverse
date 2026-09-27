# -*- coding: utf-8 -*-
"""
Multilingual news ingestion module (Module A).
Supports GDELT, RSS, and Twitter (via tweepy) with language detection.
"""
import os
import json
import logging
from typing import List, Dict
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
        "query": "*",
        "mode": "artlist",
        "format": "json",
        "maxrecords": str(max_records),
        "timespan": "24",
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("articles", [])
    except Exception as e:
        logger.error(f"GDELT fetch failed: {e}")
        return []


def _fetch_rss() -> List[Dict]:
    """Fetch headlines from a list of RSS feeds defined in .env (comma‑separated)."""
    feeds = os.getenv("COUNTERVERSE_RSS_FEEDS", "").split(",")
    headlines = []
    for feed in filter(None, feeds):
        try:
            import feedparser
            parsed = feedparser.parse(feed)
            for entry in parsed.entries[:5]:
                headlines.append({"title": entry.title, "link": entry.link})
        except Exception as e:
            logger.warning(f"RSS fetch error for {feed}: {e}")
    return headlines


def _fetch_twitter() -> List[Dict]:
    """Fetch recent tweets using Tweepy (if credentials provided)."""
    api_key = os.getenv("COUNTERVERSE_TWITTER_API_KEY")
    api_secret = os.getenv("COUNTERVERSE_TWITTER_API_SECRET")
    bearer_token = os.getenv("COUNTERVERSE_TWITTER_BEARER_TOKEN")
    if not bearer_token:
        return []
    try:
        import tweepy
        client = tweepy.Client(bearer_token=bearer_token)
        tweets = client.search_recent_tweets(query="supply chain OR semiconductor", max_results=20)
        return [{"title": t.text, "id": t.id} for t in tweets.data] if tweets.data else []
    except Exception as e:
        logger.warning(f"Twitter fetch failed: {e}")
        return []


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
    raw.extend(_fetch_twitter())
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
