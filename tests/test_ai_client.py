import pytest
from unittest.mock import MagicMock, patch
from ai_client import get_sql_from_llm


@pytest.fixture
def mock_openai_client():
    with patch("ai_client.OpenAI") as mock_openai:
        yield mock_openai


def test_get_sql_simple_extraction(mock_openai_client):
    """Test simple extraction where LLM returns just SQL."""
    mock_instance = mock_openai_client.return_value
    mock_instance.chat.completions.create.return_value.choices[
        0
    ].message.content = "SELECT * FROM charts;"

    sql = get_sql_from_llm("test question", "schema", 10)
    assert sql == "SELECT * FROM charts;"


def test_get_sql_markdown_extraction(mock_openai_client):
    """Test extraction from markdown code blocks."""
    mock_instance = mock_openai_client.return_value
    content = """
    Here is the query:
    ```sql
    SELECT * FROM charts.uk_singles_prestreaming_raw LIMIT 5;
    ```
    Hope that helps!
    """
    mock_instance.chat.completions.create.return_value.choices[
        0
    ].message.content = content

    sql = get_sql_from_llm("test question", "schema", 10)
    assert sql == "SELECT * FROM charts.uk_singles_prestreaming_raw LIMIT 5;"


def test_get_sql_xml_tag_extraction(mock_openai_client):
    """Test extraction from <sql> tags."""
    mock_instance = mock_openai_client.return_value
    content = """
    Thinking process...
    <sql>
    SELECT title FROM charts.songs WHERE artist = 'Queen';
    </sql>
    """
    mock_instance.chat.completions.create.return_value.choices[
        0
    ].message.content = content

    sql = get_sql_from_llm("test question", "schema", 10)
    assert sql == "SELECT title FROM charts.songs WHERE artist = 'Queen';"


def test_get_sql_retry_logic(mock_openai_client):
    """Test that the function retries when validation fails."""
    mock_instance = mock_openai_client.return_value

    # First response: Invalid SQL
    # Second response: Valid SQL
    mock_response_1 = MagicMock()
    mock_response_1.choices[0].message.content = "INVALID SQL"

    mock_response_2 = MagicMock()
    mock_response_2.choices[0].message.content = "SELECT * FROM valid_table"

    mock_instance.chat.completions.create.side_effect = [
        mock_response_1,
        mock_response_2,
    ]

    def validation_callback(sql):
        if "INVALID" in sql:
            return False, "Syntax Error"
        return True, None

    sql = get_sql_from_llm(
        "test question", "schema", 10, validation_callback=validation_callback
    )

    assert sql == "SELECT * FROM valid_table"
    assert mock_instance.chat.completions.create.call_count == 2


def test_get_sql_max_retries_exceeded(mock_openai_client):
    """Test that exception is raised after max retries."""
    mock_instance = mock_openai_client.return_value
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "INVALID SQL"

    # Always return invalid SQL
    mock_instance.chat.completions.create.return_value = mock_response

    def validation_callback(sql):
        return False, "Always fail"

    with pytest.raises(Exception) as excinfo:
        get_sql_from_llm(
            "test", "schema", 10, validation_callback=validation_callback, max_retries=2
        )

    assert "Failed to generate valid SQL" in str(excinfo.value)
