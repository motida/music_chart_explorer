import os
import psycopg2


def inspect_schema():
    try:
        conn = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "localhost"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            user=os.environ.get("POSTGRES_USER", "postgres"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            dbname=os.environ.get("POSTGRES_DATABASE", "musiccharts"),
        )
        cur = conn.cursor()

        print("--- Listing all relations in schema 'charts' ---")
        cur.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'charts'
        """)
        rows = cur.fetchall()
        for row in rows:
            print(f"{row[0]} ({row[1]})")

        print("\n--- Listing materialized views in schema 'charts' ---")
        cur.execute("""
            SELECT matviewname 
            FROM pg_matviews 
            WHERE schemaname = 'charts'
        """)
        rows = cur.fetchall()
        for row in rows:
            print(f"{row[0]}")

        # Specifically check our target view
        print("\n--- Columns for charts.uk_singles_prestreaming_scored ---")
        try:
            cur.execute("SELECT * FROM charts.uk_singles_prestreaming_scored LIMIT 0")
            for desc in cur.description:
                print(f"{desc.name}")
        except Exception as e:
            print(f"Error: {e}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error connecting to database: {e}")


if __name__ == "__main__":
    inspect_schema()
