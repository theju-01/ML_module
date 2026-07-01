"""Shared scenario configuration for validation and demos.

This module is intentionally constants-only so other files can import it
without triggering runtime work or import-time failures.
"""
#hyopothetical values
scenarios = [
    {
        "scenario_id": "price_10_pct",
        "parameter": "price_per_unit",
        "magnitude": 10,
        "magnitude_type": "percentage",
    },
    {
        "scenario_id": "price_20_pct",
        "parameter": "price_per_unit",
        "magnitude": 20,
        "magnitude_type": "percentage",
    },
]
#nrml range
ground_truth = {
    "price_10_pct": {
        "revenue_delta_pct": -5.0,
    },
    "price_20_pct": {
        "revenue_delta_pct": -10.0,
    },
}

__all__ = ["scenarios", "ground_truth"]