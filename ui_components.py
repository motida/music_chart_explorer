import plotly.express as px
import pandas as pd
import streamlit as st


def render_song_details(
    artist: str,
    title: str,
    artwork_url: str,
    peak_pos: int,
    weeks_on_chart: int,
    first_entry: str,
):
    """
    Renders the song details section including artwork and key metrics.
    Uses Streamlit columns to organize layout.
    """
    col_art, col_metrics = st.columns([1, 3])  # Create a 1:3 ratio for columns

    with col_art:
        if artwork_url:
            st.image(
                artwork_url,
                caption=f"{artist} - {title}",
                use_container_width=True,
            )
        else:
            # Display a placeholder if no artwork is available
            st.info("No artwork found")

    with col_metrics:
        # Create three columns for the metrics
        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Peak Position",
            f"#{peak_pos}",
            help="Best position reached on the chart.",
        )
        m2.metric(
            "Weeks on Chart",
            f"{weeks_on_chart}",
            help="Total number of weeks the song appeared in the top 100.",
        )
        m3.metric(
            "First Entry",
            f"{first_entry}",
            help="The date the song first entered the chart.",
        )


def plot_song_chart(hist_df: pd.DataFrame, title: str) -> None:
    """
    Plots the chart run for a song using Plotly.
    Handles the 'gap' logic for non-consecutive weeks to show breaks in the chart run.

    Args:
        hist_df: DataFrame containing 'from_date' and 'position' columns.
        title: Title of the chart.
    """
    if hist_df.empty:
        st.warning("No history data available to plot.")
        return

    # --- Gap Detection for Graph ---
    # This logic ensures that if a song drops out of the chart and then re-enters,
    # the line on the graph will be broken, accurately representing the chart run.

    # We work on a copy to avoid mutating the original DataFrame if it's used elsewhere
    df_plot = hist_df.copy()
    df_plot["from_date"] = pd.to_datetime(df_plot["from_date"])

    rows_with_gaps = []
    prev_date = None

    # Iterate through each week the song was on the chart
    for _, row in df_plot.iterrows():
        curr_date = row["from_date"]
        if prev_date:
            delta = (curr_date - prev_date).days
            # If the gap between chart entries is more than ~a week, insert a break.
            # We use 9 days to be safe against minor shifts in chart publication days.
            if delta > 9:
                # Insert a new row with a null position. Plotly will not connect this point.
                gap_date = prev_date + pd.Timedelta(days=7)
                rows_with_gaps.append({"from_date": gap_date, "position": None})

        rows_with_gaps.append(row.to_dict())
        prev_date = curr_date

    # Create a new DataFrame with the gaps included
    hist_df_gapped = pd.DataFrame(rows_with_gaps)

    # --- Plotly Chart ---
    # Invert the y-axis because in charts, #1 is at the top.
    fig = px.line(
        hist_df_gapped,
        x="from_date",
        y="position",
        title=title,
        markers=True,
    )

    # Explicitly tell Plotly NOT to connect points where data is missing
    fig.update_traces(connectgaps=False)

    # Reverse the y-axis so that 1 is at the top
    fig.update_yaxes(autorange="reversed")

    # Apply a dark theme and transparent background to match the app's style
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    st.plotly_chart(fig, use_container_width=True)
