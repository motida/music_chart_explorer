import streamlit as st
import pandas as pd
import os
import plotly.express as px
from database import get_connection
from ai_client import get_sql_from_llm
from styles import apply_retro_style
from dotenv import load_dotenv
from schema_definitions import SCHEMA_RAW, SCHEMA_RANKINGS

# Load environment variables from .env file
load_dotenv()

# Page Config
st.set_page_config(page_title="Music Chart Explorer", layout="wide")

# --- RETRO CSS ---
apply_retro_style()

st.title("🎵 Music Chart Explorer")
st.markdown("### > INITIALIZING DATA RETRIEVAL... 🚀")

# Get API Key from environment
api_key = os.environ.get("OPENAI_API_KEY", "")


# Database Connection


conn = get_connection()


# Schemas are now imported from schema_definitions.py


# Main UI
# Sidebar for Debugging
with st.sidebar:
    st.header("System Status")
    if conn:
        st.success("🟢 Database Online")
    else:
        st.error("🔴 Database Offline")

    if not api_key:
        api_key = st.text_input("Enter OpenAI API Key", type="password")
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
            st.rerun()

    with st.expander("Schema Viewer"):
        st.markdown("**Raw Charts**")
        st.code(SCHEMA_RAW, language="text")
        st.markdown("**Rankings (View)**")
        st.code(SCHEMA_RANKINGS, language="text")

    st.markdown("---")

# Configuration
DEFAULT_LIMIT = int(os.environ.get("SQL_LIMIT", 100))

st.markdown("### Explore the Charts")

# Example Queries
col1, col2, col3 = st.columns(3)
if col1.button("🏆 Top 5 All-Time"):
    st.session_state.question = "What are the top 5 songs of all time?"
if col2.button("⏳ Longest #1 Hits"):
    st.session_state.question = "Which songs spent the most weeks at position 1?"
if col3.button("📅 First #1 of 1980"):
    st.session_state.question = "What was the number 1 song on January 1st 1980?"

# Search Form
with st.form(key="search_form"):
    question = st.text_input(
        "Ask a question about the charts:",
        value=st.session_state.get("question", ""),
        placeholder="e.g. What are the top 5 songs of all time?",
    )
    submit_button = st.form_submit_button(label="Search")

if submit_button and question:
    if not api_key:
        st.error("Please provide an OpenAI API Key.")
        st.stop()

    # Intelligent Routing
    lower_q = question.lower()
    if any(k in lower_q for k in ["all-time", "top", "best", "most", "rank", "total"]):
        schema_context = SCHEMA_RANKINGS

    else:
        schema_context = SCHEMA_RAW

    # Generate SQL
    with st.spinner("Generating SQL..."):
        try:
            sql_query = get_sql_from_llm(question, schema_context, DEFAULT_LIMIT)
            # Clean up SQL if it contains markdown code blocks
            sql_query = (
                sql_query.replace("```sql", "").replace("```", "").strip().rstrip(";")
            )

            # --- SQL SAFETY VALIDATION ---
            forbidden_keywords = [
                "DROP",
                "DELETE",
                "INSERT",
                "UPDATE",
                "ALTER",
                "TRUNCATE",
                "GRANT",
                "REVOKE",
                "CREATE",
            ]
            normalized_sql = sql_query.upper()

            if not normalized_sql.startswith("SELECT"):
                st.error("🚨 Safety Alert: The generated query must start with SELECT.")
                st.stop()

            if any(keyword in normalized_sql for keyword in forbidden_keywords):
                st.error(
                    "🚨 Safety Alert: The generated query contains forbidden keywords. Only SELECT statements are allowed."
                )
                st.stop()

            # --- LIMIT ENFORCEMENT ---
            if "LIMIT" not in normalized_sql:
                sql_query += f" LIMIT {DEFAULT_LIMIT}"
                normalized_sql = sql_query.upper()
            else:
                # Optional: Parse and cap the limit if it's too high
                # For simplicity, we'll just ensure it's not missing.
                pass
            # -----------------------------

            with st.expander("🔍 View Generated SQL", expanded=False):
                st.code(sql_query, language="sql")

        except Exception as e:
            st.error(f"Error generating SQL: {e}")
            st.stop()

    # Execute SQL
    if conn:
        try:
            df = pd.read_sql(sql_query, conn)

            if df.empty:
                st.warning("Query returned no results.")
            else:
                # Enhanced Dataframe Display
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "position": st.column_config.NumberColumn(
                            "Rank", format="%d ⭐"
                        ),
                        "peak_position": st.column_config.NumberColumn(
                            "Peak", format="#%d"
                        ),
                        "artist": "Artist",
                        "title": "Song Title",
                        "score": st.column_config.NumberColumn(
                            "All-Time Score", format="%d pts"
                        ),
                        "weeks_in_chart": "Weeks on Chart",
                        "weeks_at_top": "Weeks at #1",
                        "from_date": st.column_config.DateColumn(
                            "Date", format="DD/MM/YYYY"
                        ),
                        "first_charted": st.column_config.DateColumn(
                            "First Entry", format="YYYY-MM-DD"
                        ),
                    },
                    hide_index=True,
                )

            # Visualization Logic
            # Check if we have artist/title columns to plot history
            if not df.empty and "artist" in df.columns and "title" in df.columns:
                # If multiple rows, let user select one, or default to first
                selected_row = 0
                if len(df) > 1:
                    options = [
                        f"{r['artist']} - {r['title']}" for i, r in df.iterrows()
                    ]
                    selected_option = st.selectbox(
                        "Select a song to visualize ranking history:", options
                    )
                    selected_row = options.index(selected_option)

                # Data is now correct: title=Song, artist=Artist
                song_title = df.iloc[selected_row]["title"]
                artist_name = df.iloc[selected_row]["artist"]

                st.markdown("---")
                st.subheader(f"📈 History: {artist_name} - {song_title}")

                # Fetch history
                history_query = """
                    SELECT from_date, to_date, position 
                    FROM charts.uk_singles_prestreaming_raw 
                    WHERE artist = %s AND title = %s 
                    ORDER BY from_date
                """
                hist_df = pd.read_sql(
                    history_query, conn, params=(artist_name, song_title)
                )

                if not hist_df.empty:
                    # Calculate Metrics
                    # ... (metrics logic kept) ...
                    peak_pos = hist_df["position"].min()
                    weeks_on_chart = len(hist_df)
                    first_entry = hist_df["from_date"].iloc[0]

                    m1, m2, m3 = st.columns(3)
                    m1.metric(
                        "Peak Position",
                        f"#{peak_pos}",
                        delta=None,
                        help="Best position reached",
                    )
                    m2.metric(
                        "Weeks on Chart",
                        f"{weeks_on_chart}",
                        help="Total weeks in top 100",
                    )
                    m3.metric(
                        "First Entry", f"{first_entry}", help="Date first entered chart"
                    )

                    # Correct Data Gaps for Plotting
                    # Ensure properly formatted dates
                    hist_df["from_date"] = pd.to_datetime(hist_df["from_date"])

                    # Create a complete weekly date range from start to finish
                    full_date_range = pd.date_range(
                        start=hist_df["from_date"].min(),
                        end=hist_df["from_date"].max(),
                        freq="7D",
                    )

                    # Reindex to insert NaNs for missing weeks
                    hist_df = (
                        hist_df.set_index("from_date")
                        .reindex(full_date_range)
                        .reset_index()
                        .rename(columns={"index": "from_date"})
                    )

                    # Plot
                    # Add a custom column for hover display (handle NaNs gracefully)
                    hist_df["week_range"] = hist_df.apply(
                        lambda x: f"{x['from_date'].date()} to {x['to_date']}"
                        if pd.notnull(x["position"])
                        else "Not in Chart",
                        axis=1,
                    )

                    fig = px.line(
                        hist_df,
                        x="from_date",
                        y="position",
                        title=f"Chart Run: {song_title}",
                        markers=True,
                        custom_data=["week_range"],
                        labels={
                            "position": "Chart Position",
                            "from_date": "Week Start Date",
                        },
                    )

                    fig.update_layout(yaxis=dict(autorange="reversed"))  # Rank 1 is top
                    fig.update_traces(
                        line_color="#1DB954",
                        line_width=3,
                        line_shape="linear",  # linear is usually better when handling gaps than 'hv' which might imply sustained position
                        connectgaps=False,  # Explicitly do NOT connect gaps
                        hovertemplate="<b>Week:</b> %{customdata[0]}<br><b>Position:</b> %{y}<extra></extra>",
                    )

                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No history found for this song.")

        except Exception as e:
            st.error(f"Error executing SQL: {e}")
