"""
M4 - Risk Score Calculator

Combines:
    - M2 ML anomaly information
    - M3 rule-based anomaly information

Output:
    Risk score from 0 to 100
"""

from typing import Optional


# Risk assigned to each M3 rule
RULE_RISK = {
    "MISSING_DATA": 80,
    "TIMESTAMP_GAP": 50,
    "SPIKE": 65,
    "FROZEN_VALUE": 70,
    "DRIFT": 70,
}

# Risk range for ML anomalies
ML_MIN_RISK = 40
ML_MAX_RISK = 60


def is_ml_anomaly(ml_prediction, ml_status=None):
    """
    Decide whether M2 detected an anomaly.

    We prefer ml_status because the new dataset contains:
        Normal
        Anomaly

    This avoids problems caused by different numeric encodings.
    """

    if ml_status is not None:
        status = str(ml_status).strip().lower()

        if status == "anomaly":
            return True

        if status == "normal":
            return False

    # Fallback for older datasets
    if ml_prediction in (1, "1"):
        return True

    # Isolation Forest style
    if ml_prediction in (-1, "-1"):
        return True

    return False


def calculate_ml_risk(
    ml_prediction,
    anomaly_score: Optional[float],
    ml_status=None,
    anomaly_floor=-0.20
):
    """
    Calculate risk caused by the ML model.
    """

    if not is_ml_anomaly(ml_prediction, ml_status):
        return 0

    # If score is missing, give minimum ML risk
    if anomaly_score is None:
        return ML_MIN_RISK

    score = float(anomaly_score)

    # More negative = stronger anomaly
    strength = abs(score) / abs(anomaly_floor)

    # Keep strength between 0 and 1
    strength = max(0.0, min(strength, 1.0))

    risk = (
        ML_MIN_RISK
        + strength * (ML_MAX_RISK - ML_MIN_RISK)
    )

    return round(risk)


def calculate_rule_risk(
    rule_anomaly,
    rule_anomaly_type: Optional[str]
):
    """
    Calculate risk caused by M3 rules.
    """

    if not rule_anomaly:
        return 0

    if not rule_anomaly_type:
        return 50

    # M3 may have multiple rules:
    # SPIKE, DRIFT
    rules = [
        rule.strip().upper()
        for rule in str(rule_anomaly_type).split(",")
        if rule.strip()
    ]

    risks = [
        RULE_RISK.get(rule, 50)
        for rule in rules
        if rule != "NORMAL"
    ]

    if not risks:
        return 0

    # If multiple rules fire, use the most serious one
    return max(risks)


def calculate_risk_score(
    ml_prediction,
    anomaly_score,
    rule_anomaly,
    rule_anomaly_type,
    ml_status=None,
    anomaly_floor=-0.20
):
    """
    Calculate final M4 risk score.

    Final risk =
        ML risk + Rule risk

    Maximum = 100
    """

    ml_risk = calculate_ml_risk(
        ml_prediction,
        anomaly_score,
        ml_status,
        anomaly_floor
    )

    rule_risk = calculate_rule_risk(
        rule_anomaly,
        rule_anomaly_type
    )

    final_risk = ml_risk + rule_risk

    return min(final_risk, 100)