from .runner import validate_model

# Backward-compatible alias used by existing imports.
validate = validate_model

__all__ = ["validate_model", "validate"]