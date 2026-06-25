"""The stable adapter interface every provider must implement.

Contract: contracts/provider.yaml — required methods are ``initialize``,
``validate``, ``execute``, ``status``. No partial implementations: an adapter
that does not implement all four cannot be instantiated.

See: SPEC-009, ADR-005 (BYOK), ADR-012 (Product Boundary).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from pipelinekit.runtime.result import StepResult


class BaseAdapter(ABC):
    """Base interface for all PipelineKit adapters.

    Every adapter is replaceable. Provider-specific code never leaks into the
    runtime or CLI. Provider errors are mapped to PK error codes before they
    leave the adapter.
    """

    @abstractmethod
    def initialize(self) -> None:
        """Prepare the adapter — validate credentials, check connectivity."""
        ...

    @abstractmethod
    def validate(self) -> StepResult:
        """Validate adapter configuration without executing."""
        ...

    @abstractmethod
    def execute(self) -> StepResult:
        """Execute the adapter's primary operation."""
        ...

    @abstractmethod
    def status(self) -> dict:
        """Return current adapter status as a structured dict."""
        ...
