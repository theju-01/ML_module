import pandas as pd
import logging


logger = logging.getLogger(__name__)


def compute(df: pd.DataFrame):
    logger.info("TEMP START compute shape=%s rows=%s cols=%s", df.shape, len(df), len(df.columns))

    df = df.copy()

    df["date"] = pd.to_datetime(
        df["date"]
    )

    monthly = (
        df.groupby(
            pd.Grouper(
                key="date",
                freq="MS",
            )
        )["revenue"]
        .sum()
        .reset_index()
    )

    monthly["month"] = (
        monthly["date"]
        .dt.strftime("%Y-%m")
    )

    monthly_revenue = [

        {
            "month": row["month"],
            "value": round(
                row["revenue"],
                2,
            ),
        }

        for _, row
        in monthly.iterrows()
    ]

    first = monthly[
        "revenue"
    ].iloc[0]

    last = monthly[
        "revenue"
    ].iloc[-1]

    growth_rate_pct = (
        (last - first)
        / first
    ) * 100

    if growth_rate_pct > 5:
        trend = "growing"

    elif growth_rate_pct < -5:
        trend = "declining"

    else:
        trend = "flat"

    kpi_cards = {
        "total_revenue": round(
            df["revenue"].sum(),
            2,
        ),
        "avg_revenue": round(
            df["revenue"].mean(),
            2,
        ),
        "total_units_sold": int(
            df["units_sold"].sum()
        ),
        "avg_price": round(
            df["price_per_unit"].mean(),
            2,
        ),
    }

    missing_ratio = (
        df.isnull()
        .mean()
        .mean()
    )

    warnings = []

    if missing_ratio > 0:

        warnings.append(
            "Dataset contains missing values"
        )

    data_quality_score = round(
        1 - missing_ratio,
        2,
    )

    logger.info(
        "TEMP END compute monthly_rows=%s trend=%s warnings=%s",
        len(monthly_revenue),
        trend,
        len(warnings),
    )

    return {
        "monthly_revenue":
            monthly_revenue,

        "growth_rate_pct":
            round(
                growth_rate_pct,
                2,
            ),

        "trend":
            trend,

        "kpi_cards":
            kpi_cards,

        "data_quality_score":
            data_quality_score,

        "warnings":
            warnings,
    }