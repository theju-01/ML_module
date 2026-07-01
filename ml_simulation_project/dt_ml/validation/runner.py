from sklearn.metrics import (
    mean_absolute_percentage_error,
    mean_squared_error,
)

import numpy as np
import logging
#this file is created to check whether the predicted reesults are matching with the actual results or not and then calculating the metrics like mape, directional accuracy and rmse to evaluate the performance of the model.


logger = logging.getLogger(__name__)

def validate_model(
    model_predict_fn,
    test_df,
    ground_truth,
    scenarios,
):
    """Validate a predictive model over a set of scenarios.

    Parameters
    - model_predict_fn: callable(test_df, parameter, magnitude, magnitude_type)
        function that returns a dict with a `predicted_kpis` mapping.
    - test_df: DataFrame used as input to the model for predictions.
    - ground_truth: mapping of `scenario_id` -> actual revenue delta (float).
    - scenarios: iterable of scenario dicts, each containing keys:
        `scenario_id`, `parameter`, `magnitude`, `magnitude_type`.

    The function runs the model for each scenario, extracts the predicted
    revenue percent change (`revenue_delta_pct`) from the model output
    (defaulting to 0 if not present), looks up the corresponding actual
    delta from `ground_truth`, and records whether the model got the
    direction (sign) correct.

    It then computes three aggregate metrics across scenarios:
    - MAPE: mean absolute percentage error between actual and predicted.
    - RMSE: root mean squared error between actual and predicted.
    - directional_accuracy: fraction of scenarios where predicted and
      actual deltas share the same sign.

    Returns a dict with rounded metric values.
    """

    logger.info(
        "TEMP START validate_model test_shape=%s scenarios=%s ground_truth=%s",
        getattr(test_df, "shape", None),
        len(scenarios),
        len(ground_truth),
    )

    results = []

    def _as_numeric_delta(value):
        """Normalize a scalar delta or KPI mapping into a numeric delta."""

        if isinstance(value, dict):
            return value.get("revenue_delta_pct", 0)
        return value

    # Iterate through each scenario and collect predicted vs actual values
    for sc in scenarios:

        # Call the provided prediction function with scenario parameters
        prediction = model_predict_fn(
            test_df,
            sc["parameter"],
            sc["magnitude"],
            sc["magnitude_type"],
        )

        # Extract the predicted revenue percent change from model output.
        # If the model did not return this KPI, default to 0.
        pred_delta = prediction[
            "predicted_kpis"
        ].get(
            "revenue_delta_pct",
            0,
        )

        # Look up the actual revenue percent change for this scenario
        actual_delta = _as_numeric_delta(ground_truth[
            sc["scenario_id"]
        ])

        # Record predicted, actual and whether the direction matches
        results.append({
            "predicted": pred_delta,
            "actual": actual_delta,
            # directional_hit is True when both have the same sign
            "directional_hit": np.sign(pred_delta) == np.sign(actual_delta),
        })

    # Compute MAPE across all scenarios
    mape = mean_absolute_percentage_error(
        [r["actual"] for r in results],
        [r["predicted"] for r in results],
    )

    # Compute RMSE across all scenarios (wrap mean_squared_error with sqrt)
    rmse = np.sqrt(
        mean_squared_error(
            [r["actual"] for r in results],
            [r["predicted"] for r in results],
        )
    )

    # Fraction of scenarios where predicted and actual directional sign match
    directional_accuracy = sum(r["directional_hit"] for r in results) / len(results)

    logger.info(
        "TEMP END validate_model results=%s mape=%s rmse=%s directional_accuracy=%s",
        len(results),
        round(mape, 4),
        round(rmse, 4),
        round(directional_accuracy, 4),
    )

    # Return rounded values for readability/consistency
    return {
        "mape": round(mape, 4),
        "rmse": round(rmse, 4),
        "directional_accuracy": round(directional_accuracy, 4),
    }