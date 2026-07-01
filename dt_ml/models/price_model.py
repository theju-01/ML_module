import numpy as np
import pandas as pd

from sklearn.linear_model import LinearRegression

from dt_ml.feature_eng import (
    validate_required_columns,
    clean_numeric_columns,
    remove_invalid_rows,
)


def predict(
    df: pd.DataFrame,
    parameter: str,
    magnitude: float,
    magnitude_type: str,
) -> dict:

    required_cols = ["price_per_unit", "units_sold"]

    validate_required_columns(df, required_cols)

    df = clean_numeric_columns(df, required_cols)

    df = remove_invalid_rows(df)

    df = df[
        (df["price_per_unit"] > 0)
        & (df["units_sold"] > 0)
    ]

    if len(df) < 5:
        raise ValueError("Not enough valid data for training.")

    price = df["price_per_unit"].values
    units = df["units_sold"].values

    # LOG-LOG REGRESSION
    X = np.log(price).reshape(-1, 1)
    y = np.log(units)

    model = LinearRegression()

    model.fit(X, y)

    elasticity = model.coef_[0]

    r2_score = model.score(X, y)

    # PRICE CHANGE FACTOR
    if magnitude_type == "percentage":
        factor = 1 + (magnitude / 100)
    else:
        factor = (
            (price.mean() + magnitude)
            / price.mean()
        )

    new_price_factor = factor

    # DEMAND RESPONSE
    new_units_factor = new_price_factor ** elasticity

    revenue_old = float((price * units).sum())

    revenue_new =float( (
        price
        * new_price_factor
        * units
        * new_units_factor
    ).sum())

    revenue_delta_abs = float(revenue_new - revenue_old)

    revenue_delta_pct =float(
        ( (revenue_new / revenue_old) - 1
    ) * 100)

    # SIMPLE CHURN ESTIMATE
    churn_delta_pct = (
        max(0, abs(magnitude) * 0.25)
        if magnitude > 0
        else 0
    )

    confidence = float(min(
        95.0,
        max(40.0, r2_score * 100)
    )
    )
    

    return {
    "predicted_kpis": {
        "revenue_delta_pct": round(revenue_delta_pct, 2),
        "revenue_delta_abs": round(revenue_delta_abs, 2),
        "churn_delta_pct": round(churn_delta_pct, 2),
        "growth_rate_new": None,
    },
    "confidence_score": round(confidence, 1),
    "model_used": "price_elasticity_linreg",
    "model_version": "v1",
}