import os
import psycopg2
import streamlit as st


@st.cache_resource
def _create_connection():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            dbname=os.environ.get("POSTGRES_DATABASE", "musiccharts"),
            sslmode=os.environ.get(
                "POSTGRES_SSLMODE", "prefer"
            ),  # Default to 'prefer' for local compatibility, 'require' for prod
        )
        return conn
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        return None


def get_connection():
    """
    Retrieves a robust database connection, automatically reconnecting if the
    cached connection is dead.
    """
    conn = _create_connection()

    # Check if connection is None (failed initially) or closed
    force_reconnect = False
    if conn is None or conn.closed != 0:
        force_reconnect = True
    else:
        # Deep check: Try executing a simple query
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        except psycopg2.Error as e:
            # Check for "current transaction is aborted" (25P02)
            if e.pgcode == "25P02":
                conn.rollback()
            else:
                # For other errors (OperationalError, etc.), force reconnect
                force_reconnect = True

    if force_reconnect:
        # Clear cache and retry
        _create_connection.clear()
        conn = _create_connection()

    return conn
