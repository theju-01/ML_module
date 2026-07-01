"""Compatibility wrapper for the shared validation implementation.

Keep this module as a stable import target for older code while delegating the
actual logic to dt_ml.validation.runner.
"""

from .runner import validate_model

__all__ = ["validate_model"]
