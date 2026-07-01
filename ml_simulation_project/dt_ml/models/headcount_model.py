import pandas as pd


def predict(
    df,
    parameter,
    magnitude,
    magnitude_type,
):

    if "salary" not in df.columns:
        raise ValueError(
            "salary column missing"
        )

    avg_salary = df["salary"].mean()

    current_headcount = len(df)

    if magnitude_type == "percentage":

        new_headcount = (
            current_headcount
            * (1 + magnitude / 100)
        )

    else:

        new_headcount = (
            current_headcount
            + magnitude
        )

    cost_delta_abs = (
        new_headcount
        - current_headcount
    ) * avg_salary

    total_current_cost = (
        avg_salary * current_headcount
    )

    cost_delta_pct = (
        cost_delta_abs
        / total_current_cost
    ) * 100

    return {
        "predicted_kpis": {
            "cost_delta_abs": round(
                cost_delta_abs,
                2,
            ),
            "cost_delta_pct": round(
                cost_delta_pct,
                2,
            ),
            "growth_rate_new": None,
        },
        "confidence_score": 70.0,
        "model_used": "headcount_linear",
        "model_version": "v1",
    }