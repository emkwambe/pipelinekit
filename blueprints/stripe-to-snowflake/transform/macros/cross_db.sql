-- cross_db.sql
-- Cross-database portability macros for Blueprint #003 (stripe-to-snowflake).
-- These let the same staging models build against Snowflake (prod/dev) and
-- DuckDB (local verification) — and BigQuery — without per-adapter SQL forks.
-- The macro dispatches on target.type at compile time. See
-- docs/CROSS_DB_COMPATIBILITY.md for the pattern.

{% macro to_timestamp(column) %}
  {% if target.type == 'snowflake' %}
    to_timestamp_ntz({{ column }})
  {% elif target.type == 'duckdb' %}
    to_timestamp({{ column }})
  {% elif target.type == 'bigquery' %}
    TIMESTAMP_SECONDS({{ column }})
  {% else %}
    CAST({{ column }} AS TIMESTAMP)
  {% endif %}
{% endmacro %}

{% macro safe_boolean(column) %}
  {% if target.type == 'duckdb' %}
    ({{ column }} = 'true')
  {% else %}
    COALESCE(TRY_CAST({{ column }} AS BOOLEAN), false)
  {% endif %}
{% endmacro %}
