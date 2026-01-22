import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def create_materialized_view():
    """
    Creates the materialized view charts.uk_singles_prestreaming_scored.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            dbname=os.environ.get("POSTGRES_DATABASE", "musiccharts"),
            sslmode=os.environ.get("POSTGRES_SSLMODE", "prefer"),
        )
        with conn.cursor() as cur:
            cur.execute(
                "DROP MATERIALIZED VIEW IF EXISTS charts.uk_singles_prestreaming_scored;"
            )
            cur.execute("""
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
            conn.commit()
            print(
                "Successfully created materialized view charts.uk_singles_prestreaming_scored."
            )
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error creating materialized view: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    create_materialized_view()
