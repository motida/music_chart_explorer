import duckdb
import streamlit as st
from config import config


@st.cache_resource(show_spinner=False)
def get_connection():
    """
    Retrieves a read-only connection to the local DuckDB database.
    """
    try:
        conn = duckdb.connect(config.DUCKDB_PATH, read_only=True)
        return conn
    except Exception as e:
        st.error(f"Failed to connect to DuckDB database: {e}")
        return None
