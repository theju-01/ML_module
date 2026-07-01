"""Validation thresholds used to decide whether a model meets quality
expectations. Each mapping holds numeric thresholds for evaluation metrics.

Keys:
- `mape`: maximum acceptable mean absolute percentage error (lower is better)
- `directional_accuracy`: minimum acceptable fraction of scenarios where
  the model predicts the correct direction (sign) of the change.
"""

# Thresholds for the price model validation
PRICE_MODEL_THRESHOLDS = {
    "mape": 0.18,
    "directional_accuracy": 0.80,
}

# Thresholds for the headcount model validation
HEADCOUNT_MODEL_THRESHOLDS = {
    "mape": 0.25,
    "directional_accuracy": 0.70,
}

# Thresholds for the marketing model validation
MARKETING_MODEL_THRESHOLDS = {
    "mape": 0.20,
    "directional_accuracy": 0.75,
}