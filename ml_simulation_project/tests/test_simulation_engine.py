import pandas as pd

from dt_ml.simulation_engine import run


def test_price_model_runs():

    df = pd.read_csv("data/sales_data.csv")

    result = run(
        df=df,
        decision_type="price_change",
        parameter="price_per_unit",
        magnitude=10,
        magnitude_type="percentage",
    )

    assert "predicted_kpis" in result

    assert "confidence_score" in result

    assert "model_used" in result

    assert result["model_used"] == "price_elasticity_linreg"