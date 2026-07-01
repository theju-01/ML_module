import pandas as pd
import logging

from dt_ml.models.price_model import predict as price_predict
from dt_ml.models.headcount_model import predict as headcount_predict
from dt_ml.models.marketing_model import predict as marketing_predict


logger = logging.getLogger(__name__)


DISPATCH = {
    "price_change": price_predict,
    "headcount": headcount_predict,
    "marketing": marketing_predict,
}


def summarize_baseline(df: pd.DataFrame):
    logger.info("TEMP START summarize_baseline shape=%s rows=%s cols=%s", df.shape, len(df), len(df.columns))

    revenue = 0

    if (
        "price_per_unit" in df.columns
        and "units_sold" in df.columns
    ):
        revenue = float((
            df["price_per_unit"]
            * df["units_sold"]
        ).sum())

    return {
        "estimated_revenue": float(round(revenue, 2)),
        "rows": len(df),
    }


def project_after(
    baseline: dict,
    prediction: dict,
):
    logger.info(
        "TEMP START project_after baseline_keys=%s prediction_keys=%s",
        list(baseline.keys()),
        list(prediction.keys()),
    )

    revenue_before = baseline["estimated_revenue"]

    revenue_delta = prediction["predicted_kpis"].get(
        "revenue_delta_abs",
        0,
    )

    revenue_after = float(revenue_before + revenue_delta)

    return {
        "estimated_revenue": float(round(revenue_after, 2))
    }


def run(
    df: pd.DataFrame,
    decision_type: str,
    parameter: str,
    magnitude: float,
    magnitude_type: str,
):
    logger.info(
        "TEMP START run decision_type=%s parameter=%s magnitude=%s magnitude_type=%s shape=%s",
        decision_type,
        parameter,
        magnitude,
        magnitude_type,
        df.shape,
    )

    if decision_type not in DISPATCH:
        raise ValueError(
            f"Unknown decision_type: {decision_type}"
        )

    model_function = DISPATCH[decision_type]

    result = model_function(
        df=df,
        parameter=parameter,
        magnitude=magnitude,
        magnitude_type=magnitude_type,
    )

    baseline = summarize_baseline(df)

    result["deltas"] = {
        "before": baseline,
        "after": project_after(
            baseline,
            result,
        ),
    }

    logger.info("TEMP END run result_keys=%s", list(result.keys()))

    return result