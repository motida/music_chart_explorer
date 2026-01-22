import pytest
from unittest.mock import patch, MagicMock
from create_view import create_materialized_view


@pytest.fixture
def mock_psycopg2_connect():
    with patch("psycopg2.connect") as mock_connect:
        yield mock_connect


def test_create_materialized_view_success(mock_psycopg2_connect):
    """Test that the materialized view is created successfully."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_psycopg2_connect.return_value = mock_conn
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    create_materialized_view()

    mock_cursor.execute.assert_any_call(
        "DROP MATERIALIZED VIEW IF EXISTS charts.uk_singles_prestreaming_scored;"
    )
    mock_cursor.execute.assert_any_call("""
                CREATE MATERIALIZED VIEW charts.uk_singles_prestreaming_scored AS
                WITH song_weeks AS (
                    SELECT
                        artist,
                        title,
                        from_date,
                        position,
                        (1.0 / position) * 100 AS score_per_week
                    FROM
                        charts.uk_singles_prestreaming_raw
                )
                SELECT
                    artist,
                    title,
                    SUM(score_per_week)::bigint AS score,
                    MIN(from_date) AS first_charted,
                    MIN(position) AS peak_position,
                    COUNT(CASE WHEN position = 1 THEN 1 END) AS weeks_at_top,
                    COUNT(*) AS weeks_in_chart
                FROM
                    song_weeks
                GROUP BY
                    artist,
                    title;
            """)
    mock_conn.commit.assert_called_once()
    mock_conn.close.assert_called_once()


def test_create_materialized_view_exception(mock_psycopg2_connect):
    """Test that an exception is handled correctly."""
    mock_psycopg2_connect.side_effect = Exception("Test Exception")

    with patch("builtins.print") as mock_print:
        create_materialized_view()
        mock_print.assert_called_with(
            "Error creating materialized view: Test Exception"
        )
