# Music Chart Explorer

## Project Overview

The **Music Chart Explorer** is a Python-based data visualization application built with **Streamlit**. It allows users to explore historical UK Singles Chart data using natural language queries. The application leverages **OpenAI's GPT-3.5** to convert user questions into SQL queries, which are executed against a **PostgreSQL** database. Results are visualized using **Plotly**.

## Architecture

*   **Frontend:** Streamlit (`main.py`)
*   **Database:** PostgreSQL (Schema: `charts`)
*   **AI Engine:** OpenAI API (GPT-3.5 Turbo) for Text-to-SQL
*   **Data Processing:** Pandas
*   **Visualization:** Plotly Express

## Prerequisites

Before running the application, ensure you have the following:

1.  **Python 3.x** installed.
2.  A running **PostgreSQL** database instance populated with chart data.
3.  An **OpenAI API Key**.

### Environment Variables

Create a `.env` file in the project root with the following keys:

```ini
OPENAI_API_KEY=your_openai_api_key
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DATABASE=musiccharts
```

## Setup & Installation

1.  **Create a virtual environment (optional but recommended):**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

To start the Streamlit application:

```bash
streamlit run main.py
```

The application will typically be accessible at `http://localhost:8501`.

## Database Management Scripts

*   **`inspect_schema.py`**: Connects to the database and lists all tables and materialized views within the `charts` schema. Useful for verifying the database structure.
    ```bash
    python inspect_schema.py
    ```

*   **`create_view.py`**: Creates a materialized view named `charts.artist_song_rankings` to aggregate song performance data (weeks on chart, peak position, etc.).
    ```bash
    python create_view.py
    ```

## Schemas
*   `charts.uk_singles_prestreaming_raw`: Raw chart positions.
*   `charts.uk_singles_prestreaming_scored`: Materialized view with calculated scores and rankings.
