SCHEMA_RAW = """
Table: charts.uk_singles_prestreaming_raw
Columns:
- id (integer)
- from_date (date)
- to_date (date)
- position (integer): The rank on the chart (1 is best).
- artist (text): The name of the artist or band.
- title (text): The name of the song.
- label (text): Record label.
"""

SCHEMA_RANKINGS = """
Table: charts.uk_singles_prestreaming_scored
Columns:
- artist (text): The name of the artist or band.
- title (text): The name of the song.
- score (bigint): A calculated score for all-time ranking.
- first_charted (date): Date the song first entered the chart.
- peak_position (smallint): Best position reached (1 is best).
- weeks_at_top (bigint): Number of weeks at position 1.
- weeks_in_chart (bigint): Total weeks spent on the chart.
"""

SCHEMA_ALL = SCHEMA_RAW + "\n" + SCHEMA_RANKINGS
