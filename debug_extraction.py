import re


def extract_sql_v1(raw_response):
    # The logic currently in ai_client.py

    # 1. Regex
    code_block_match = re.search(
        r"```(?:[\w\s]*)\n(.*?)```", raw_response, re.DOTALL | re.IGNORECASE
    )
    if code_block_match:
        return "REGEX_MATCH", code_block_match.group(1).strip()

    # 2. Fallback
    sql_query = raw_response.strip()
    if sql_query.startswith("```"):
        parts = sql_query.split("\n", 1)
        if len(parts) > 1:
            sql_query = parts[1]
        else:
            sql_query = sql_query.lstrip("`")

    if sql_query.endswith("```"):
        sql_query = sql_query.rstrip("`").rstrip()

    if sql_query.lower().startswith("sql"):
        sql_query = sql_query[3:].strip()

    return "FALLBACK", sql_query


# Test Cases
test_cases = {
    "log_case": """```sql
SELECT artist, title, weeks_at_top 
FROM charts.uk_singles_prestreaming_scored 
WHERE first_charted BETWEEN '1980-01-01' AND '1989-12-31'
ORDER BY weeks_at_top DESC 
LIMIT 1;
```""",
    "log_case_crlf": """```sql\r
SELECT artist, title, weeks_at_top \r
FROM charts.uk_singles_prestreaming_scored \r
WHERE first_charted BETWEEN '1980-01-01' AND '1989-12-31'\r
ORDER BY weeks_at_top DESC \r
LIMIT 1;\r
```""",
    "no_markdown": "SELECT * FROM charts;",
    "leading_text": "Here is the query:\nSELECT * FROM charts;",
    "trailing_text": "SELECT * FROM charts;\nHere is the query:",
    "xml_tags": "<sql>SELECT * FROM charts;</sql>",
}

for name, case in test_cases.items():
    print(f"{name}: {extract_sql_v1(case)}")
