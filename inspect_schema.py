import duckdb
from config import config


def inspect_schema():
    print(f"Inspecting DuckDB database at: {config.DUCKDB_PATH}")
    try:
        conn = duckdb.connect(config.DUCKDB_PATH, read_only=True)
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'charts'"
        ).fetchall()
        print("\\nTables in schema 'charts':")
        for table in tables:
            print(f"- {table[0]}")

        columns = conn.execute(
            "SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'charts' ORDER BY table_name, ordinal_position"
        ).fetchall()
        print("\\nColumns:")
        for col in columns:
            print(f"  {col[0]}.{col[1]} ({col[2]})")

    except Exception as e:
        print(f"Error connecting to DuckDB database: {e}")


if __name__ == "__main__":
    inspect_schema()
