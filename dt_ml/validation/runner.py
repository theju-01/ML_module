from sklearn.metrics import (
    mean_absolute_percentage_error,
    mean_squared_error,
)

import numpy as np


def validate_model(
    model_predict_fn,
    test_df,
    ground_truth,
    scenarios,
):

    results = []

    for sc in scenarios:

        prediction = model_predict_fn(
            test_df,
            sc["parameter"],
            sc["magnitude"],
            sc["magnitude_type"],
        )

        pred_delta = prediction[
            "predicted_kpis"
        ].get(
            "revenue_delta_pct",
            0,
        )

        actual_delta = ground_truth[
            sc["scenario_id"]
        ]

        results.append({

            "predicted": pred_delta,

            "actual": actual_delta,

            "directional_hit":
                np.sign(pred_delta)
                ==
                np.sign(actual_delta),
        })

    mape = mean_absolute_percentage_error(
        [r["actual"] for r in results],
        [r["predicted"] for r in results],
    )

    rmse = np.sqrt(
        mean_squared_error(
            [r["actual"] for r in results],
            [r["predicted"] for r in results],
        )
    )

    directional_accuracy = sum(
        r["directional_hit"]
        for r in results
    ) / len(results)

    return {
        "mape": round(mape, 4),
        "rmse": round(rmse, 4),
        "directional_accuracy": round(
            directional_accuracy,
            4,
        ),
    }