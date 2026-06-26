"""Adapter capability registry — the deterministic bound on AI proposals.

The ``BlueprintProposer`` consults this registry **before** any AI call so the
system never proposes a blueprint for a connector the dlt adapter cannot
execute (ADR-018: "AI must not invent unsupported connector behavior"). An
unsupported source or destination fails fast with ``PK-GEN-006`` — never wasting
an AI call (ADR-008, deterministic before AI).

This is a static declaration of what the adapter layer supports, not a live
probe. Adding a connector here is a deliberate, reviewed change.
"""

from __future__ import annotations

SUPPORTED_SOURCES: dict[str, dict] = {
    "postgres": {
        "dlt_source": "sql_database",
        "credential_fields": ["host", "port", "database", "user", "password"],
        "tables": "configurable",
    },
    "salesforce": {
        "dlt_source": "salesforce",
        "credential_fields": ["username", "password", "security_token"],
        "tables": ["accounts", "opportunities", "contacts", "leads", "cases"],
    },
    "stripe": {
        "dlt_source": "stripe_analytics",
        "credential_fields": ["api_key"],
        "tables": [
            "charges",
            "customers",
            "subscriptions",
            "invoices",
            "events",
            "refunds",
        ],
    },
}

SUPPORTED_DESTINATIONS: dict[str, dict] = {
    "snowflake": {
        "dlt_destination": "snowflake",
        "credential_fields": ["account", "user", "password", "database", "warehouse"],
    },
    "bigquery": {
        "dlt_destination": "bigquery",
        "credential_fields": ["project", "dataset", "credentials_path"],
    },
    "duckdb": {
        "dlt_destination": "duckdb",
        "credential_fields": ["path"],
    },
}


class AdapterCapabilityRegistry:
    """What the dlt adapter layer can actually execute (read-only)."""

    def is_source_supported(self, source_type: str) -> bool:
        """Return True if the source type has a registered dlt adapter."""
        return source_type in SUPPORTED_SOURCES

    def is_destination_supported(self, destination_type: str) -> bool:
        """Return True if the destination type has a registered dlt adapter."""
        return destination_type in SUPPORTED_DESTINATIONS

    def get_source_info(self, source_type: str) -> dict:
        """Return the capability record for a source, or ``{}`` if unsupported."""
        return SUPPORTED_SOURCES.get(source_type, {})

    def get_destination_info(self, destination_type: str) -> dict:
        """Return the capability record for a destination, or ``{}``."""
        return SUPPORTED_DESTINATIONS.get(destination_type, {})

    def get_supported_tables(self, source_type: str) -> list[str] | str:
        """Return the supported tables for a source.

        Returns the literal string ``"configurable"`` for sources that accept
        any table (e.g. postgres), or a concrete list for fixed-schema sources.
        Returns an empty list for an unsupported source.
        """
        info = self.get_source_info(source_type)
        tables: list[str] | str = info.get("tables", [])
        return tables

    def supported_source_names(self) -> list[str]:
        """Return the list of supported source type names."""
        return list(SUPPORTED_SOURCES.keys())

    def supported_destination_names(self) -> list[str]:
        """Return the list of supported destination type names."""
        return list(SUPPORTED_DESTINATIONS.keys())
