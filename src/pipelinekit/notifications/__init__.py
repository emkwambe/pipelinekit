"""Notification system: structured, actionable alerts dispatched after a run.

A pipeline that fails silently cannot be trusted. Every failure produces a
human-readable message plus structured evidence (for Phase 4 AI diagnostics).
Notification failures never block pipeline state recording (SPEC-008).
"""
