from pathlib import Path

import pandas as pd
from dt_ml.risk_scorer import score
from config import ground_truth, scenarios
from dt_ml.simulation_engine import run
from dt_ml.validation import validate_model


PROJECT_ROOT = Path(__file__).resolve().parents[1]         #searches where the mentioned file is present


def load_dataset(file_path):
    """Load a CSV file into a pandas DataFrame."""

    return pd.read_csv(file_path)


def price_model_wrapper(test_df, parameter, magnitude, magnitude_type):
    """Wrap the simulation engine with the price-change scenario inputs."""
#learns the mapping of price in the market and profit or lose for the company.
    return run(
        df=test_df,
        decision_type="price_change",
        parameter=parameter,
        magnitude=magnitude,
        magnitude_type=magnitude_type,
    )


def run_validation():
    """Run validation using the shared scenario and ground-truth config."""
#here validation takes place by comparing the predicted results with the actual results and then calculating the metrics like mape, directional accuracy and rmse.
    test_df = load_dataset(PROJECT_ROOT / "data" / "sales_data.csv")
    return validate_model(
        test_df=test_df,
        scenarios=scenarios,
        ground_truth=ground_truth,
        model_predict_fn=price_model_wrapper,
    )

def test_low_risk_prediction():
    # Test case for a low-risk prediction
    prediction = {
        "predicted_kpis": {
            "revenue_delta_pct": 5,
            "churn_delta_pct": 1,
            "cost_delta_pct": 2,
        },
        "confidence_score": 80,
    }
    result = score(decision_type="price_change", magnitude=10, prediction=prediction)
    assert result["risk_level"] == "Low"
    assert result["risk_score"] == 0

def test_medium_risk_prediction():
    # Test case for a medium-risk prediction
    prediction = {
        "predicted_kpis": {
            "revenue_delta_pct": -5,
            "churn_delta_pct": 3,
            "cost_delta_pct": 15,
        },
        "confidence_score": 50,
    }
    result = score(decision_type="price_change", magnitude=15, prediction=prediction)
    assert result["risk_level"] == "Medium"
    assert result["risk_score"] > 0 and result["risk_score"] <= 66

def test_high_risk_prediction():
    # Test case for a high-risk prediction
    prediction = {
        "predicted_kpis": {
            "revenue_delta_pct": -10,
            "churn_delta_pct": 5,
            "cost_delta_pct": 20,
        },
        "confidence_score": 30,
    }
    result = score(decision_type="price_change", magnitude=30, prediction=prediction)
    assert result["risk_level"] == "High"
    assert result["risk_score"] > 66
