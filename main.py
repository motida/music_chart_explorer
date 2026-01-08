import streamlit as st
import pandas as pd
import os
import plotly.express as px
from database import get_connection
from ai_client import get_sql_from_llm
from artwork_client import get_artwork_url
from styles import apply_retro_style
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

    # Generate SQL
    with st.spinner("Analyzing your request..."):
        try:
            sql_query = get_sql_from_llm(question, SCHEMA_ALL, DEFAULT_LIMIT)
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
            st.error(f"An error occurred: {e}")
            st.session_state.search_results = None


# --- RENDER RESULTS (Persisted State) ---

if st.session_state.generated_sql:
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

                # Gap Detection for Graph
                # Insert None/NaN rows if weeks are skipped so Plotly breaks the line
                hist_df["from_date"] = pd.to_datetime(hist_df["from_date"])

                rows_with_gaps = []
                prev_date = None

                for _, row in hist_df.iterrows():
                    curr_date = row["from_date"]
                    if prev_date:
                        delta = (curr_date - prev_date).days
                        # If gap is > 9 days (accounting for potential chart day shifts), insert break
                        if delta > 9:
                            gap_date = prev_date + pd.Timedelta(days=7)
                            # Append a row with None position to break the line
                            rows_with_gaps.append(
                                {"from_date": gap_date, "position": None}
                            )

                    rows_with_gaps.append(row.to_dict())
                    prev_date = curr_date

                hist_df_gapped = pd.DataFrame(rows_with_gaps)

                # Layout: Artwork + Metrics
                col_art, col_metrics = st.columns([1, 3])

                with col_art:
                    if artwork_url:
                        st.image(
                            artwork_url,
                            caption=f"{artist_name} - {song_title}",
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

                # Plotly Chart
                # Invert y-axis for ranking (1 is top)
                fig = px.line(
                    hist_df_gapped,
                    x="from_date",
                    y="position",
                    title=f"Chart Run: {song_title}",
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
