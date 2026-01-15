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
    1. Search MusicBrainz for a "Release Group" matching the artist and title.
       - Prioritize type "Single".
    2. Use the MusicBrainz ID (MBID) to fetch the front cover from
       the Cover Art Archive.
    """
    if not artist or not title:
        return None

    try:
        # 1. Search for Release Group
        mbid = _search_musicbrainz_release_group(artist, title)
        if not mbid:
            return None

        # 2. Fetch Cover Art
        return _get_cover_art_archive_url(mbid)

    except Exception as e:
        logging.error(f"Error fetching artwork: {e}")
        return None


def _search_musicbrainz_release_group(artist, title):
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

        response = requests.get(url, params=params, headers=headers, timeout=5)
        response.raise_for_status()
        data = response.json()

        if not data.get("release-groups"):
            return None

        # Filter/Prioritize
        # We want "Single" primary type if possible

        best_mbid = None
        # found_single = False

        for rg in data["release-groups"]:
            # Check score (0-100)
            if int(rg.get("score", 0)) < 80:
                continue

            primary_type = rg.get("primary-type")
            mbid = rg.get("id")

            if primary_type == "Single":
                best_mbid = mbid
                break  # Found a single, stop looking (results are usually sorted by relevance/score)

            # Keep the first album/EP result as fallback if we haven't found a single yet
            if not best_mbid:
                best_mbid = mbid

        return best_mbid

    except Exception as e:
        logging.error(f"MusicBrainz Search Error: {e}")
        return None


def _get_cover_art_archive_url(mbid):
    # Try to get the 500px front image
    # https://coverartarchive.org/release-group/{mbid}/front-500

    # Note: Cover Art Archive usually maps Release Group -> Release -> Image
    # 'release-group' endpoint redirects to the 'release' image

    url = f"https://coverartarchive.org/release-group/{mbid}/front-500"

    try:
        response = requests.head(url, timeout=3, allow_redirects=True)
        if response.status_code == 200:
            return url

        # If 404, try generic 'front' (might be original size)
        url_fallback = f"https://coverartarchive.org/release-group/{mbid}/front"
        response = requests.head(url_fallback, timeout=3, allow_redirects=True)
        if response.status_code == 200:
            return url_fallback

        return None

    except Exception as e:
        logging.error(f"Cover Art Archive Error: {e}")
        return None
