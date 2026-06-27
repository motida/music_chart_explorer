import duckdb


def init_db():
    conn = duckdb.connect("musiccharts.duckdb")

    # Create schema
    conn.execute("CREATE SCHEMA IF NOT EXISTS charts;")

    # Create the raw table
    conn.execute("DROP TABLE IF EXISTS charts.uk_singles_prestreaming_raw;")
    conn.execute("""
        CREATE TABLE charts.uk_singles_prestreaming_raw (
            id INTEGER,
            from_date DATE,
            to_date DATE,
            position INTEGER,
            artist VARCHAR,
            title VARCHAR,
            label VARCHAR
        );
    """)

    # Load data from TSV
    # Postgres COPY format uses \\N for NULL and tab delimiter
    print("Loading raw data into DuckDB...")
    conn.execute("""
        COPY charts.uk_singles_prestreaming_raw FROM 'music_data.tsv' 
        (DELIMITER '\\t', HEADER FALSE, NULL '\\N');
    """)

    # Create the "materialized view" as a table
    print("Calculating scores and rankings...")
    conn.execute("DROP TABLE IF EXISTS charts.uk_singles_prestreaming_scored;")
    conn.execute("""
        CREATE TABLE charts.uk_singles_prestreaming_scored AS
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
            CAST(SUM(score_per_week) AS BIGINT) AS score,
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

    print("DuckDB database created successfully: musiccharts.duckdb")


if __name__ == "__main__":
    init_db()
