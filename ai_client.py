import os
import logging
import re
from openai import OpenAI

from database import get_connection

# Configure logging
logging.basicConfig(
    filename="sql_generation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def get_sql_from_llm(question, schema_context, limit, max_retries=5):
    api_key = os.environ.get("OPENAI_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url)

    # Allow overriding max_retries via env var
    max_retries = int(os.environ.get("SQL_MAX_RETRIES", max_retries))

    system_prompt = f"""
    You are a PostgreSQL expert. Convert the user's natural language question into a valid SQL query.
    
    Context:
    {schema_context}
    
    Rules:
    1. Return ONLY the SQL query. No markdown, no explanations.
    2. Use the full table names provided in the context (e.g., charts.uk_singles_prestreaming_raw).
    3. Be careful with string matching - use ILIKE for case-insensitive searches and remember all text data is UPPERCASE.
    4. Limit results to {limit} unless specified otherwise by the user.
    5. Always select `artist`, `title`, and context columns if available (e.g., `peak_position`, `weeks_in_chart`, `weeks_at_top` for rankings; `position`, `from_date` for raw charts).
    6. DATE LOGIC: Charts are weekly. If the user asks about a specific date, find the week containing it:
       - CORRECT: `WHERE '1980-01-01' BETWEEN from_date AND to_date`
       - WRONG: `WHERE from_date = '1980-01-01'`
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    last_error = None

    for attempt in range(max_retries):
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"),
            messages=messages,
            temperature=0,
        )

        raw_response = response.choices[0].message.content.strip()

        # Improved SQL Extraction
        # 1. Try to find content within <sql> tags (common in reasoning models)
        sql_match = re.search(
            r"<sql>(.*?)</sql>", raw_response, re.DOTALL | re.IGNORECASE
        )
        if sql_match:
            sql_query = sql_match.group(1).strip()
        else:
            # 2. Try to find content within markdown code blocks
            # Matches ``` followed by optional lang, optional newline/space, then content, then ```
            code_block_match = re.search(
                r"```(?:[\w\s]*)\n(.*?)```", raw_response, re.DOTALL | re.IGNORECASE
            )
            if code_block_match:
                sql_query = code_block_match.group(1).strip()
            else:
                # 3. Fallback: aggressive cleanup
                sql_query = raw_response.strip()
                if sql_query.startswith("```"):
                    # Split by newline and drop the first line if it looks like a language tag
                    parts = sql_query.split("\n", 1)
                    if len(parts) > 1:
                        sql_query = parts[1]
                    else:
                        sql_query = sql_query.lstrip("`")

                if sql_query.endswith("```"):
                    sql_query = sql_query.rstrip("`").rstrip()

        # Post-cleanup: Sometimes "sql" lingers if regex was imperfect
        if sql_query.lower().startswith("sql"):
            sql_query = sql_query[3:].strip()

        cleaned_sql = sql_query

        # Validation Step
        conn = get_connection()
        if not conn:
            # If DB is unavailable, we cannot validate. Return what we have.
            logging.warning(
                f"DB Unavailable. Question: {question} -> Generated SQL: {cleaned_sql}"
            )
            return cleaned_sql

        try:
            with conn.cursor() as cur:
                # EXPLAIN parses and plans the query without executing it, checking for syntax/schema errors
                cur.execute(f"EXPLAIN {cleaned_sql}")

            # If we get here, SQL is valid
            logging.info(
                f"SUCCESS. Question: {question} -> Generated SQL: {cleaned_sql}"
            )
            return cleaned_sql

        except Exception as e:
            # Important: Rollback the transaction if EXPLAIN failed,
            # otherwise the connection remains in an aborted state.
            conn.rollback()
            last_error = str(e)
            logging.error(
                f"FAILURE. Question: {question} -> Generated SQL: {cleaned_sql} -> Error: {last_error}"
            )
            # Feedback to LLM
            messages.append({"role": "assistant", "content": sql_query})
            messages.append(
                {
                    "role": "user",
                    "content": f"The previous query was invalid and returned this error: {last_error}. Please provide a corrected SQL query following the original rules.",
                }
            )
            # Continue to next iteration

    # If retries exhausted
    logging.critical(f"GAVE UP. Question: {question} -> Last Error: {last_error}")
    raise Exception(
        f"Failed to generate valid SQL after {max_retries} attempts. Last error: {last_error}"
    )
