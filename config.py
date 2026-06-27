import os
from dotenv import load_dotenv

# Load environment variables from .env file once
load_dotenv()


class Config:
    # OpenAI Settings
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    SQL_MAX_RETRIES = int(os.environ.get("SQL_MAX_RETRIES", "5"))

    # Database Settings
    DUCKDB_PATH = os.environ.get("DUCKDB_PATH", "musiccharts.duckdb")

    # App Settings
    SHOW_SQL_DEBUG = os.environ.get("SHOW_SQL_DEBUG", "False").lower() in (
        "true",
        "1",
        "t",
    )

    # External API Settings
    USER_AGENT = os.environ.get(
        "USER_AGENT", "MusicChartExplorer/1.0 ( motigpt@example.com )"
    )


config = Config()
