"""
M4 - Risk Score Calculator

Combines:
    - M2 Isolation Forest evidence
    - M3 rule-based evidence

Output:
    Risk score from 0 to 100
"""

from typing import Optional


# Project-defined risk values for M3 rules
RULE_RISK = {
    "MISSING_DATA": 80,
    "TIMESTAMP_GAP": 50,
    "SPIKE": 65,
    "FROZEN_VALUE": 70,
    "DRIFT": 70,
}


# ML anomaly risk range
ML_MIN_RISK = 40
ML_MAX_RISK = 60


def calculate_ml_risk(
    ml_prediction: int,
    anomaly_score: Optional[float],
    anomaly_floor: float = -0.05
) -> int:
    """
    Convert Isolation Forest anomaly evidence
    into a risk score.

    Normal ML prediction:
        0 -> risk 0

    ML anomaly:
        1 -> risk between 40 and 60
    """

    if ml_prediction != 1:
        return 0

    # If score is unavailable, use minimum ML risk
    if anomaly_score is None:
        return ML_MIN_RISK

    anomaly_score = float(anomaly_score)

    # Isolation Forest:
    # more negative score = stronger anomaly
    strength = abs(anomaly_score) / abs(anomaly_floor)

    # Keep strength between 0 and 1
    strength = max(0.0, min(strength, 1.0))

    risk = (
        ML_MIN_RISK
        + strength * (ML_MAX_RISK - ML_MIN_RISK)
    )

    return round(risk)


def calculate_rule_risk(
    rule_anomaly: bool,
    rule_anomaly_type: Optional[str]
) -> int:
    """
    Calculate risk from M3 rule results.

    If multiple rules are triggered,
    the highest-risk rule is used.
    """

    if not rule_anomaly:
        return 0

    if not rule_anomaly_type:
        return 50

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

    return max(risks)


def calculate_risk_score(
    ml_prediction: int,
    anomaly_score: Optional[float],
    rule_anomaly: bool,
    rule_anomaly_type: Optional[str],
    anomaly_floor: float = -0.05
) -> int:
    """
    Calculate final M4 risk score.

    ML and rule evidence are combined.
    Final score is capped at 100.
    """

    ml_risk = calculate_ml_risk(
        ml_prediction,
        anomaly_score,
        anomaly_floor
    )

    rule_risk = calculate_rule_risk(
        rule_anomaly,
        rule_anomaly_type
    )

    final_risk = ml_risk + rule_risk

    return min(final_risk, 100)