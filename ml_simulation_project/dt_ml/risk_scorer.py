import logging


logger = logging.getLogger(__name__)


def score(decision_type, magnitude, prediction):
    logger.info(
        "TEMP START score decision_type=%s magnitude=%s prediction_keys=%s",
        decision_type,
        magnitude,
        list(prediction.keys()) if isinstance(prediction, dict) else type(prediction).__name__,
    )
    #score function is a simple rule-based system that assigns a risk score based on the predicted KPIs and confidence score. 
    # It considers factors such as the magnitude of the decision, predicted changes in revenue and churn, and the confidence level of the prediction. The final risk score is categorized into Low, Medium, or High risk levels, with an explanation of the contributing factors.
    risk_score = 0
    factors = []

    predicted_kpis = prediction.get("predicted_kpis", {})
    confidence = prediction.get("confidence_score", 100)
    revenue_delta_pct = predicted_kpis.get("revenue_delta_pct", 0)
    churn_delta_pct = predicted_kpis.get("churn_delta_pct", 0)
    cost_delta_pct = predicted_kpis.get("cost_delta_pct", 0)

    if abs(magnitude) > 10:
        risk_score += 20
        factors.append("Magnitude > 10%")

    if abs(churn_delta_pct) > 2:
        risk_score += 25
        factors.append("Churn delta > 2%")

    if revenue_delta_pct < 0:
        risk_score += 15
        factors.append("Revenue delta negative")

    if confidence < 60:
        risk_score += 5
        factors.append("Confidence < 60")

    if confidence < 50:
        risk_score += 35
        factors.append("Confidence < 50")

    if confidence < 40:
        risk_score += 15
        factors.append("Confidence < 40")

    if abs(magnitude) >= 25:
        risk_score += 15
        factors.append("Magnitude > 25%")

    if decision_type == "headcount" and magnitude < -20:
        risk_score += 40
        factors.append("Large layoff > 20 employees")

    if decision_type == "marketing" and magnitude > 20000:
        risk_score += 35
        factors.append("Marketing spend spike > 20k")

    if decision_type in ["headcount", "marketing"] and cost_delta_pct > 10:
        risk_score += 10
        factors.append("Cost delta > 10% of revenue")

    risk_score = min(risk_score, 100)

    if risk_score <= 33:
        level = "Low"
    elif risk_score <= 66:
        level = "Medium"
    else:
        level = "High"

    explanation = (
        f"{level} risk decision because: {', '.join(factors)}"
        if factors
        else f"{level} risk decision because no major risk factors were triggered."
    )

    logger.info("TEMP END score risk_level=%s risk_score=%s factors=%s", level, risk_score, len(factors))

    return {
        "risk_level": level,
        "risk_score": risk_score,
        "risk_factors": factors,
        "explanation": explanation,
    }