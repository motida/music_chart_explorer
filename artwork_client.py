import requests
import streamlit as st
import time
import logging

# User Agent is required by MusicBrainz API
# See: https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting
USER_AGENT = "MusicChartExplorer/1.0 ( motigpt@example.com )"


@st.cache_data(
    show_spinner=False, ttl=3600 * 24 * 7
)  # Increased TTL, invalidates previous cache
def get_artwork_url(artist: str, title: str) -> str:
    """
    Fetches the URL of the album artwork for a given artist and song title
    using MusicBrainz and the Cover Art Archive.

    Strategy:
    1. Search MusicBrainz for a list of candidate "Release Groups" matching the artist and title.
       - Prioritize type "Single", then "Album", etc.
    2. Iterate through candidates and try to fetch the front cover from
       the Cover Art Archive.
    3. Return the first valid URL found.
    """
    if not artist or not title:
        return None

    try:
        # 1. Search for Release Group Candidates
        candidates = _search_musicbrainz_candidates(artist, title)
        if not candidates:
            return None

        # 2. Iterate and Fetch Cover Art
        for mbid in candidates:
            url = _get_cover_art_archive_url(mbid)
            if url:
                return url
            # Tiny sleep to be nice to Cover Art Archive if we are hammering it
            time.sleep(0.1)

        return None

    except Exception as e:
        logging.error(f"Error fetching artwork: {e}")
        return None


def _search_musicbrainz_candidates(artist, title):
    """
    Returns a list of MBIDs for release groups, sorted by preference:
    1. Perfect matches (score ~100) and type 'Single'
    2. Perfect matches (score ~100) and type 'Album'
    3. Other high-scoring matches
    """
    if not USER_AGENT:
        raise ValueError("USER_AGENT not found in environment variables.")
    url = "https://musicbrainz.org/ws/2/release-group"

    # lucene search query
    query = f'artist:"{artist}" AND releasegroup:"{title}"'

    params = {
        "query": query,
        "fmt": "json",
    }
    headers = {"User-Agent": USER_AGENT}

    try:
        # Respect rate limiting (1 req/sec)
        time.sleep(1.0)

        # Retry logic for MusicBrainz (sometimes it resets connection)
        for attempt in range(2):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=5)
                response.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == 1:
                    raise e
                time.sleep(1.0)

        data = response.json()

        if not data.get("release-groups"):
            return []

        singles = []
        others = []

        for rg in data["release-groups"]:
            # Check score (0-100)
            if int(rg.get("score", 0)) < 80:
                continue

            primary_type = rg.get("primary-type")
            mbid = rg.get("id")

            if primary_type == "Single":
                singles.append(mbid)
            else:
                others.append(mbid)

        # Return concatenated list: Singles first, then others
        return singles + others

    except Exception as e:
        logging.error(f"MusicBrainz Search Error: {e}")
        return []


def _get_cover_art_archive_url(mbid):
    # Try to get the 500px front image
    # https://coverartarchive.org/release-group/{mbid}/front-500

    # Standard endpoints to try
    # 1. front-500 (Preferred size)
    # 2. front (Original size, fallback)

    urls_to_try = [
        f"https://coverartarchive.org/release-group/{mbid}/front-500",
        f"https://coverartarchive.org/release-group/{mbid}/front",
    ]

    for url in urls_to_try:
        try:
            # Short timeout, follow redirects
            response = requests.head(url, timeout=3, allow_redirects=True)
            if response.status_code == 200:
                return url
        except Exception as e:
            # Just log and continue to next format/candidate
            logging.debug(f"Failed to fetch {url}: {e}")
            continue

    return None
