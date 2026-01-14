import pandas as pd
from unittest.mock import patch
from ui_components import plot_song_chart


def test_plot_song_chart_gap_logic():
    """Test that gaps are inserted for non-consecutive weeks."""
    # Create data with a gap: Week 1, Week 2, [Gap], Week 4
    data = {
        "from_date": ["2020-01-01", "2020-01-08", "2020-01-22"],
        "position": [1, 2, 5],
    }
    df = pd.DataFrame(data)

    with (
        patch("ui_components.st.plotly_chart"),
        patch("ui_components.px.line") as mock_px_line,
    ):
        # We need to capture the DataFrame passed to px.line
        plot_song_chart(df, "Test Chart")

        args, _ = mock_px_line.call_args
        df_passed = args[0]

        # Expecting 4 rows: 3 original + 1 gap
        assert len(df_passed) == 4

        # The 3rd row (index 2) should be the gap
        # Week 1 (01-01) -> Week 2 (01-08) -> Gap (01-15) -> Week 4 (01-22)
        # Note: The logic appends the gap AFTER the previous date.
        # Loop 1: 01-01. Prev=None.
        # Loop 2: 01-08. Delta=7. No gap. Prev=01-08.
        # Loop 3: 01-22. Delta=14. Gap inserted at 01-08 + 7 = 01-15.

        # Let's inspect the dates
        dates = pd.to_datetime(df_passed["from_date"]).sort_values().tolist()
        assert dates[0].strftime("%Y-%m-%d") == "2020-01-01"
        assert dates[1].strftime("%Y-%m-%d") == "2020-01-08"
        assert dates[2].strftime("%Y-%m-%d") == "2020-01-15"  # The inserted gap
        assert dates[3].strftime("%Y-%m-%d") == "2020-01-22"

        # Check that the gap row has None position
        # We can find the row with date 2020-01-15
        gap_row = df_passed[df_passed["from_date"] == "2020-01-15"]
        assert pd.isna(gap_row["position"].values[0])


def test_plot_song_chart_empty():
    """Test handling of empty dataframe."""
    df = pd.DataFrame()
    with patch("ui_components.st.warning") as mock_warn:
        plot_song_chart(df, "Title")
        mock_warn.assert_called_once()
