"""Intelligence layer: AI-assisted diagnostics.

Deterministic first, AI second. The AI layer *interprets* evidence produced by
the deterministic systems (contracts, quality, state); it never defines truth,
never executes actions, and never modifies production. Every output validates
against ``schemas/diagnostic.schema.json`` before reaching the user.

See: SPEC-005, ADR-007, ADR-014, docs/ai/PIPELINEKIT-AI & Model Strategy Standard.
"""
