from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dt_ml.risk_scorer import score

def test_small_price_change_should_be_low_risk():
    prediction = {
        "predicted_kpis": {"revenue_delta_pct": 2, "churn_delta_pct": 0.5},
        "confidence_score": 85
    }
    risk = score("price_change", 3, prediction)
    assert risk["risk_level"] == "Low"
    assert risk["risk_score"] <= 33

def test_large_price_increase_should_be_high_risk():
    prediction = {
        "predicted_kpis": {"revenue_delta_pct": -8, "churn_delta_pct": 3.5},
        "confidence_score": 55
    }
    risk = score("price_change", 25, prediction)
    assert risk["risk_level"] == "High"
    assert risk["risk_score"] >= 67

def test_negative_revenue_triggers_risk():
    prediction = {
        "predicted_kpis": {"revenue_delta_pct": -5, "churn_delta_pct": 1},
        "confidence_score": 75
    }
    risk = score("price_change", 10, prediction)
    assert "Revenue delta negative" in risk["risk_factors"]

def test_low_confidence_increases_risk():
    prediction = {
        "predicted_kpis": {"revenue_delta_pct": 10, "churn_delta_pct": 0},
        "confidence_score": 45
    }
    risk = score("price_change", 5, prediction)
    assert risk["risk_score"] >= 40

def test_high_churn_triggers_max_risk():
    prediction = {
        "predicted_kpis": {"revenue_delta_pct": 15, "churn_delta_pct": 5},
        "confidence_score": 80
    }
    risk = score("price_change", 8, prediction)
    assert "Churn delta > 2%" in risk["risk_factors"]
    assert risk["risk_score"] >= 25

def test_multiple_factors_stack():
    prediction = {
        "predicted_kpis": {"revenue_delta_pct": -12, "churn_delta_pct": 3},
        "confidence_score": 35
    }
    risk = score("price_change", 15, prediction)
    assert len(risk["risk_factors"]) >= 3
    assert risk["risk_level"] == "High"

def test_hiring_small_number_low_risk():
    prediction = {
        "predicted_kpis": {"revenue_delta_pct": 5, "cost_delta_pct": 8},
        "confidence_score": 70
    }
    risk = score("headcount", 5, prediction)
    assert risk["risk_level"] in ["Low", "Medium"]

def test_massive_layoff_high_risk():
    prediction = {
        "predicted_kpis": {"revenue_delta_pct": -20, "cost_delta_pct": -15},
        "confidence_score": 60
    }
    risk = score("headcount", -100, prediction)
    assert risk["risk_level"] == "High"