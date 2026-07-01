import pandas as pd

from dt_ml.models.price_model import predict as price_predict
from dt_ml.models.headcount_model import predict as headcount_predict
from dt_ml.models.marketing_model import predict as marketing_predict

#dispatch table for decision types to model functions
DISPATCH = {
    "price_change": price_predict,
    "headcount": headcount_predict,
    "marketing": marketing_predict,
}

# This function summarizes the baseline KPIs from the input dataframe.
#  It calculates the estimated revenue based on price per unit and units sold, and counts the number of rows
def summarize_baseline(df: pd.DataFrame):

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

# This function projects the KPIs after applying the predicted deltas from the model.
#  It takes the baseline KPIs and the model's predicted deltas, 
# and calculates the new estimated revenue by adding the revenue delta to the baseline revenue. 
# The result is returned as a dictionary with the updated estimated revenue.
def project_after(
    baseline: dict,
    prediction: dict,
):

    revenue_before = baseline["estimated_revenue"]

    revenue_delta = prediction["predicted_kpis"].get(
        "revenue_delta_abs",
        0,
    )

    revenue_after = float(revenue_before + revenue_delta)

    return {
        "estimated_revenue": float(round(revenue_after, 2))
    }


# This function runs the simulation by taking the input dataframe and the decision parameters.
# It first checks if the provided decision type is valid and retrieves the corresponding model function from the dispatch table.
# Then, it calls the model function with the input parameters to get the predicted KPIs.
#KPI stands for Key Performance Indicator, which is a measurable value that demonstrates how effectively a company is achieving key business objectives.
# After obtaining the predicted KPIs, it summarizes the baseline KPIs from the input dataframe and projects the new KPIs after applying the predicted deltas.

def run(
    df: pd.DataFrame,
    decision_type: str,
    parameter: str,
    magnitude: float,
    magnitude_type: str,
):

    if decision_type not in DISPATCH:
        raise ValueError(
            f"Unknown decision_type: {decision_type}"
        )

    model_function = DISPATCH[decision_type]

    result = model_function(
        df=df,
        parameter=parameter,
        magnitude=magnitude,
        magnitude_type=magnitude_type,    #copy and send it to me in whatsapp
    )

    baseline = summarize_baseline(df)

    result["deltas"] = {
        "before": baseline,
        "after": project_after(
            baseline,
            result,
        ),
    }

    return result

