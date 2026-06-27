-- cross_db.sql
-- Cross-database portability macros (PipelineKit blueprint pattern).
-- These let the same models build against Snowflake (prod/dev), DuckDB (local
-- verification), and BigQuery without per-adapter SQL forks. The macro dispatches
-- on target.type at compile time. See docs/CROSS_DB_COMPATIBILITY.md.

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
