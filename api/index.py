from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import duckdb
from ai_client import get_sql_from_llm
from artwork_client import get_artwork_url
from config import config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    sql: str
    data: list[dict]
    metrics: dict | None = None
    history: list[dict] | None = None
    artwork_url: str | None = None
    error: str | None = None


def get_db():
    return duckdb.connect(config.DUCKDB_PATH, read_only=True)


def format_val(val):
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return "" if val is None else val


@app.get("/api/health")
def health():
    return {"status": "ok", "db": config.DUCKDB_PATH}


@app.post("/api/query", response_model=QueryResponse)
def handle_query(req: QueryRequest):
    try:
        conn = get_db()

        def validate_sql(sql: str):
            try:
                conn.execute(f"EXPLAIN {sql}")
                return True, None
            except Exception as e:
                return False, str(e)

        # Generate SQL
        sql_query = get_sql_from_llm(
            question=req.query,
            schema_context="""Table: charts.uk_singles_prestreaming_scored
Columns:
- artist (text)
- title (text)
- score (bigint)
- first_charted (date)
- peak_position (integer)
- weeks_at_top (integer)
- weeks_in_chart (integer)""",
            limit=50,
            max_retries=config.SQL_MAX_RETRIES,
            validation_callback=validate_sql,
        )

        # Execute Query
        result = conn.execute(sql_query)
        columns = [desc[0] for desc in result.description]
        rows = result.fetchall()

        data = [
            {col: format_val(val) for col, val in zip(columns, row)} for row in rows
        ]

        metrics = None
        history = None
        artwork_url = None

        # If user searched for a specific song or artist, fetch details for the top result
        if data and "artist" in columns and "title" in columns:
            top_row = data[0]
            artist_name = str(top_row["artist"])
            song_title = str(top_row["title"])

            history_query = """
                SELECT from_date, to_date, position 
                FROM charts.uk_singles_prestreaming_raw 
                WHERE artist = ? AND title = ? 
                ORDER BY from_date
            """
            hist_result = conn.execute(history_query, [artist_name, song_title])
            hist_columns = [desc[0] for desc in hist_result.description]
            hist_rows = hist_result.fetchall()

            history = [
                {col: format_val(val) for col, val in zip(hist_columns, row)}
                for row in hist_rows
            ]

            if history:
                # Metrics
                metrics = {
                    "peak": min(int(row["position"]) for row in history),
                    "weeks": len(history),
                    "debut": str(history[0]["from_date"]),
                }

            # Artwork
            artwork_url = get_artwork_url(artist_name, song_title)

        return QueryResponse(
            sql=sql_query,
            data=data,
            metrics=metrics,
            history=history,
            artwork_url=artwork_url,
        )

    except Exception as e:
        return QueryResponse(sql="", data=[], error=str(e))
