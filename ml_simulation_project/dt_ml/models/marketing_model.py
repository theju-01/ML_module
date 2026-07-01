def predict(
    df,
    parameter,
    magnitude,
    magnitude_type,
):

    if (
        "budget" not in df.columns
        or
        "conversions" not in df.columns
    ):
        raise ValueError(
            "Required marketing columns missing"
        )

    spend = df["budget"].sum()

    conversions = df["conversions"].sum()

    if magnitude_type == "percentage":

        new_spend = (
            spend
            * (1 + magnitude / 100)
        )

    else:

        new_spend = spend + magnitude

    spend_factor = (
        new_spend / spend
    ) ** 0.5

    new_conversions = (
        conversions * spend_factor
    )

    new_customers_delta = (
        new_conversions
        - conversions
    )

    cac_new = (
        new_spend
        / new_conversions
    )

    return {
        "predicted_kpis": {
            "new_customers_delta": round(
                new_customers_delta,
                0,
            ),
            "cac_new": round(
                cac_new,
                2,
            ),
            "growth_rate_new": None,
        },
        "confidence_score": 65.0,
        "model_used": "marketing_sqrt_response",
        "model_version": "v1",
    }