import pytest
from unittest.mock import patch, MagicMock
from artwork_client import (
    get_artwork_url,
    _search_musicbrainz_release_group,
    _get_cover_art_archive_url,
)


@pytest.fixture
def mock_requests_get():
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_requests_head():
    with patch("requests.head") as mock_head:
        yield mock_head


def test_search_release_group_found(mock_requests_get):
    """Test finding a release group successfully."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "release-groups": [
            {"id": "mbid1", "primary-type": "Album", "score": 90},
            {"id": "mbid2", "primary-type": "Single", "score": 95},
        ]
    }
    mock_response.raise_for_status.return_value = None
    mock_requests_get.return_value = mock_response

    mbid = _search_musicbrainz_release_group("Artist", "Song")
    assert mbid == "mbid2"  # Should prioritize Single


def test_search_release_group_none_found(mock_requests_get):
    """Test when no release group is found."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"release-groups": []}
    mock_requests_get.return_value = mock_response

    mbid = _search_musicbrainz_release_group("Artist", "Song")
    assert mbid is None


def test_get_cover_art_url_success(mock_requests_head):
    """Test getting a valid cover art URL."""
    mock_requests_head.return_value.status_code = 200

    url = _get_cover_art_archive_url("fake_mbid")
    assert url == "https://coverartarchive.org/release-group/fake_mbid/front-500"


def test_get_cover_art_url_fallback(mock_requests_head):
    """Test fallback to non-500px URL if 500px is missing."""
    # First call 404, Second call 200
    mock_requests_head.side_effect = [
        MagicMock(status_code=404),
        MagicMock(status_code=200),
    ]

    url = _get_cover_art_archive_url("fake_mbid")
    assert url == "https://coverartarchive.org/release-group/fake_mbid/front"


def test_get_artwork_url_integration(mock_requests_get, mock_requests_head):
    """Test the main public function."""
    # Mock MB search
    mock_mb_response = MagicMock()
    mock_mb_response.json.return_value = {
        "release-groups": [{"id": "mbid_test", "primary-type": "Single", "score": 100}]
    }
    mock_requests_get.return_value = mock_mb_response

    # Mock Cover Art check
    mock_requests_head.return_value.status_code = 200

    url = get_artwork_url("Artist", "Title")
    assert url == "https://coverartarchive.org/release-group/mbid_test/front-500"
