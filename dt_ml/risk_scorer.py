def score(
    decision_type,
    magnitude,
    prediction,
):

    risk_score = 0

    factors = []

    if abs(magnitude) > 10:

        risk_score += 20

        factors.append(
            "Large magnitude"
        )

    confidence = prediction.get(
        "confidence_score",
        100,
    )

    if confidence < 60:

        risk_score += 20

        factors.append(
            "Low confidence"
        )

    if risk_score <= 33:

        level = "Low"

    elif risk_score <= 66:

        level = "Medium"

    else:

        level = "High"

    return {
        "risk_level": level,
        "risk_score": risk_score,
        "risk_factors": factors,
        "explanation":
            f"{level} risk decision",
    }