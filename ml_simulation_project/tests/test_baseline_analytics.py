import pandas as pd

from dt_ml.baseline_analytics import compute


def test_baseline_runs():

    df = pd.read_csv(
        "data/sales_data.csv"
    )


    result = compute(df)

    assert "monthly_revenue" in result

    assert "growth_rate_pct" in result

    assert "kpi_cards" in result


