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
    """
    col_art, col_metrics = st.columns([1, 3])

    with col_art:
        if artwork_url:
            st.image(
                artwork_url,
                caption=f"{artist} - {title}",
                use_container_width=True,
            )
        else:
            st.info("No artwork found")

    with col_metrics:
        m1, m2, m3 = st.columns(3)
        m1.metric(
            "Peak Position",
            f"#{peak_pos}",
            help="Best position reached",
        )
        m2.metric(
            "Weeks on Chart",
            f"{weeks_on_chart}",
            help="Total weeks in top 100",
        )
        m3.metric(
            "First Entry",
            f"{first_entry}",
            help="Date first entered chart",
        )


def plot_song_chart(hist_df: pd.DataFrame, title: str) -> None:
    """
    Plots the chart run for a song using Plotly.
    Handles the 'gap' logic for non-consecutive weeks.

    Args:
        hist_df: DataFrame containing 'from_date' and 'position' columns.
        title: Title of the chart.
    """
    if hist_df.empty:
        st.warning("No history data available to plot.")
        return

    # Gap Detection for Graph
    # Insert None/NaN rows if weeks are skipped so Plotly breaks the line
    # We work on a copy to avoid mutating the original DF if it's used elsewhere
    df_plot = hist_df.copy()
    df_plot["from_date"] = pd.to_datetime(df_plot["from_date"])

    rows_with_gaps = []
    prev_date = None

    for _, row in df_plot.iterrows():
        curr_date = row["from_date"]
        if prev_date:
            delta = (curr_date - prev_date).days
            # If gap is > 9 days (accounting for potential chart day shifts), insert break
            if delta > 9:
                gap_date = prev_date + pd.Timedelta(days=7)
                # Append a row with None position to break the line
                rows_with_gaps.append({"from_date": gap_date, "position": None})

        rows_with_gaps.append(row.to_dict())
        prev_date = curr_date

    hist_df_gapped = pd.DataFrame(rows_with_gaps)

    # Plotly Chart
    # Invert y-axis for ranking (1 is top)
    fig = px.line(
        hist_df_gapped,
        x="from_date",
        y="position",
        title=title,
        markers=True,
    )
    # Explicitly tell Plotly NOT to connect gaps (though None usually does this)
    fig.update_traces(connectgaps=False)
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
