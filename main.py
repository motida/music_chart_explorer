import streamlit as st
import pandas as pd
import os

from database import get_connection
from ai_client import get_sql_from_llm
from artwork_client import get_artwork_url
from styles import apply_retro_style
from ui_components import plot_song_chart, render_song_details
from dotenv import load_dotenv
from schema_definitions import SCHEMA_ALL

# Load environment variables from .env file
load_dotenv()

# Page Config
st.set_page_config(
    page_title="Music Chart Explorer",
    page_icon="🎵",
    layout="wide",
)

# Apply Custom CSS
apply_retro_style()


# Database Connection
@st.cache_resource(show_spinner=False)
def get_conn():
    return get_connection()


try:
    conn = get_conn()
except Exception as e:
    st.error(f"Failed to connect to database: {e}")
    st.stop()


# --- HEADER ---
st.title("Music Chart Explorer")
st.markdown(
    "Try: *'What were the top 5 songs of 1985?'* or *'How many weeks was Bohemian Rhapsody at #1?'*"
)


# --- CONFIGURATION ---
api_key = os.environ.get("OPENAI_API_KEY")
show_sql_debug = os.getenv("SHOW_SQL_DEBUG", "False").lower() in ("true", "1", "t")
DEFAULT_LIMIT = 50

if not api_key:
    st.warning("⚠️ OPENAI_API_KEY not found in environment variables.")
    # Option: Allow input in main area if critical?
    # For now, just warning. Code below checks if not api_key: st.stop()


# --- MAIN SEARCH INPUT ---
with st.form("search_form"):
    question = st.text_input(
        "Search Query",
        label_visibility="collapsed",
        placeholder="Ask about UK Singles Chart history...",
        help="Example: 'Who had the most number ones in the 80s?'",
    )
    submit_button = st.form_submit_button(label="Explore Charts", type="primary")


# --- LOGIC & STATE MANAGEMENT ---

# Initialize Session State
if "search_results" not in st.session_state:
    st.session_state.search_results = None
if "generated_sql" not in st.session_state:
    st.session_state.generated_sql = None
if "last_question" not in st.session_state:
    st.session_state.last_question = ""


# Handling Form Submission
if submit_button and question:
    if not api_key:
        st.error("Please provide an OpenAI API Key.")
        st.stop()

    st.session_state.last_question = question

    # Define Validation Callback
    def validate_sql_callback(sql: str):
        """
        Validates SQL using EXPLAIN in the database.
        Returns: (is_valid: bool, error_message: str)
        """
        if not conn:
            return False, "Database unavailable"

        try:
            with conn.cursor() as cur:
                cur.execute(f"EXPLAIN {sql}")
            return True, None
        except Exception as e:
            conn.rollback()
            return False, str(e)

    # Generate SQL
    with st.spinner("Analyzing your request..."):
        try:
            sql_query = get_sql_from_llm(
                question,
                SCHEMA_ALL,
                DEFAULT_LIMIT,
                validation_callback=validate_sql_callback,
            )
            # Clean up SQL if it contains markdown
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

            st.session_state.generated_sql = sql_query

            # Validate Safety
            if not sql_query.lower().strip().startswith("select"):
                st.error("For safety, only SELECT queries are allowed.")
                st.session_state.search_results = None
            else:
                # Execute Query
                df = pd.read_sql(sql_query, conn)
                st.session_state.search_results = df

        except Exception as e:
            if 'relation "charts.uk_singles_prestreaming_scored" does not exist' in str(
                e
            ):
                st.error(
                    "The `charts.uk_singles_prestreaming_scored` materialized view does not exist. Please run the `create_view.py` script to create it."
                )
            else:
                st.error(f"An error occurred: {e}")
            st.session_state.search_results = None


# --- RENDER RESULTS (Persisted State) ---

if st.session_state.generated_sql and show_sql_debug:
    with st.expander("View Generated SQL (Debug)", expanded=False):
        st.code(st.session_state.generated_sql, language="sql")

if st.session_state.search_results is not None:
    df = st.session_state.search_results

    if df.empty:
        st.warning("No results found for your query.")
    else:
        st.success(f"Found {len(df)} results")

        # Enhanced Dataframe Display
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "position": st.column_config.NumberColumn("Rank", format="%d"),
                "peak_position": st.column_config.NumberColumn("Peak", format="#%d"),
                "artist": "Artist",
                "title": "Song Title",
                "score": st.column_config.NumberColumn(
                    "All-Time Score", format="%d pts"
                ),
                "weeks_in_chart": "Weeks on Chart",
                "weeks_at_top": "Weeks at #1",
            },
            hide_index=True,
        )

    # Visualization Logic
    # Check if we have artist/title columns to plot history
    if not df.empty and "artist" in df.columns and "title" in df.columns:
        # If multiple rows, let user select one, or default to first
        options = [f"{r['artist']} - {r['title']}" for i, r in df.iterrows()]

        # Use a unique key for the selectbox so it doesn't conflict
        selected_option = st.selectbox(
            "Select a song to visualize ranking history:", options, key="song_selector"
        )

        if selected_option:
            selected_row = options.index(selected_option)
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
            hist_df = pd.read_sql(history_query, conn, params=(artist_name, song_title))

            if not hist_df.empty:
                # Calculate Metrics
                peak_pos = hist_df["position"].min()
                weeks_on_chart = len(hist_df)
                first_entry = hist_df["from_date"].iloc[0]

                # Fetch Artwork
                artwork_url = get_artwork_url(artist_name, song_title)

                # Render Details
                render_song_details(
                    artist_name,
                    song_title,
                    artwork_url,
                    peak_pos,
                    weeks_on_chart,
                    first_entry,
                )

                # Plotly Chart
                plot_song_chart(hist_df, f"Chart Run: {song_title}")
