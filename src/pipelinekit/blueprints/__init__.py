"""Blueprint engine: register, validate, and describe analytics blueprints.

A blueprint is not a connector — it is a complete, reproducible analytics
system (ingestion, transformation, contracts, quality, alerts, docs). The
engine delegates execution to the runtime; it never calls adapters directly
(SPEC-006).
"""
