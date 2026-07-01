def check_price_plausibility(magnitude, risk):
    issues = []
    if abs(magnitude) < 5 and risk["risk_level"] == "High":
        issues.append(f"Small price change {magnitude}% produced High Risk")
    if abs(magnitude) > 20 and risk["risk_level"] == "Low":
        issues.append(f"Large price change {magnitude}% produced Low Risk")
    if magnitude < 0 and risk["risk_score"] > 80:
        issues.append(f"Price decrease {magnitude}% produced very high risk score")
    return issues

def check_headcount_plausibility(magnitude, risk):
    issues = []
    if magnitude > 0 and magnitude < 10 and risk["risk_score"] > 70:
        issues.append(f"Hiring {magnitude} people produced risk score {risk['risk_score']}")
    if magnitude < -20 and risk["risk_level"] != "High":
        issues.append(f"Layoff of {abs(magnitude)} people not marked as High Risk")
    if magnitude > 50 and risk["risk_score"] < 50:
        issues.append(f"Large hire of {magnitude} people produced only {risk['risk_score']} risk score")
    return issues

def check_marketing_plausibility(magnitude, risk):
    issues = []
    if magnitude > 0 and magnitude < 1000 and risk["risk_score"] > 60:
        issues.append(f"Small spend increase ${magnitude} produced risk score {risk['risk_score']}")
    if magnitude < -5000 and risk["risk_level"] == "Low":
        issues.append(f"Large budget cut ${abs(magnitude)} produced Low Risk")
    if magnitude > 20000 and risk["risk_score"] < 70:
        issues.append(f"Massive spend increase ${magnitude} not marked High Risk")
    return issues

def check_general_plausibility(risk):
    issues = []
    if risk["risk_score"] > 90 and len(risk["risk_factors"]) < 2:
        issues.append(f"High risk score {risk['risk_score']} but only {len(risk['risk_factors'])} factors triggered")
    if risk["risk_score"] < 10 and len(risk["risk_factors"]) > 3:
        issues.append(f"Low risk score {risk['risk_score']} but {len(risk['risk_factors'])} factors triggered")
    return issues

def check_all_plausibility(decision_type, magnitude, risk):
    issues = []
    issues.extend(check_general_plausibility(risk))
    
    if decision_type == "price_change":
        issues.extend(check_price_plausibility(magnitude, risk))
    elif decision_type == "headcount":
        issues.extend(check_headcount_plausibility(magnitude, risk))
    elif decision_type == "marketing":
        issues.extend(check_marketing_plausibility(magnitude, risk))
    
    return issues