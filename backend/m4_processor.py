"""
M4 - Main Processor

Combines:
    M2 ML results
    M3 rule results

Produces:
    - Risk score
    - Confidence
    - Severity
    - Explanation
    - Overall station health
    - Feature-level health
"""

from risk_score import calculate_risk_score
from explanations import generate_explanation
from health_score import (
    FEATURES,
    update_overall_health,
    update_feature_health
)


# Project-defined confidence values for rules
RULE_CONFIDENCE = {
    "MISSING_DATA": 0.98,
    "TIMESTAMP_GAP": 0.95,
    "SPIKE": 0.90,
    "FROZEN_VALUE": 0.95,
    "DRIFT": 0.90,
}


def calculate_confidence(
    ml_prediction,
    anomaly_score,
    rule_anomaly,
    rule_anomaly_type,
    anomaly_floor=-0.05
):
    """
    Calculate project-defined confidence/evidence strength.

    Important:
    These values are not calibrated probabilities.
    """

    # --------------------------------------------------
    # RULE CONFIDENCE
    # --------------------------------------------------

    if rule_anomaly and rule_anomaly_type:

        rules = [
            rule.strip().upper()
            for rule in str(rule_anomaly_type).split(",")
            if rule.strip()
        ]

        confidence_values = [
            RULE_CONFIDENCE.get(rule, 0.85)
            for rule in rules
            if rule != "NORMAL"
        ]

        if confidence_values:
            return max(confidence_values)

    # --------------------------------------------------
    # ML CONFIDENCE
    # --------------------------------------------------

    if ml_prediction == 1:

        if anomaly_score is None:
            return 0.70

        strength = (
            abs(float(anomaly_score))
            / abs(anomaly_floor)
        )

        strength = max(
            0.0,
            min(strength, 1.0)
        )

        confidence = (
            0.70
            + (strength * 0.29)
        )

        return round(confidence, 2)

    # --------------------------------------------------
    # NORMAL
    # --------------------------------------------------

    return 1.0


def calculate_severity(risk_score):
    """
    Convert risk score into severity level.
    """

    if risk_score <= 19:
        return "LOW"

    elif risk_score <= 39:
        return "MEDIUM"

    elif risk_score <= 59:
        return "HIGH"

    elif risk_score <= 79:
        return "VERY HIGH"

    else:
        return "CRITICAL"


def process_row(
    row,
    previous_health=100,
    feature_health=None,
    anomaly_floor=-0.05
):
    """
    Process one M2 + M3 record.
    """

    # --------------------------------------------------
    # READ M2 DATA
    # --------------------------------------------------

    ml_prediction = int(row["ml_prediction"])

    anomaly_score = row["anomaly_score"]

    try:
        anomaly_score = float(anomaly_score)

    except (ValueError, TypeError):
        anomaly_score = None

    # --------------------------------------------------
    # READ M3 DATA
    # --------------------------------------------------

    rule_value = row["rule_anomaly"]

    # Safely handle "True"/"False" strings
    if isinstance(rule_value, str):

        rule_anomaly = (
            rule_value.strip().lower() == "true"
        )

    else:
        rule_anomaly = bool(rule_value)

    rule_anomaly_type = row["rule_anomaly_type"]
    rule_feature = row["rule_feature"]
    rule_reason = row["rule_reason"]

    # --------------------------------------------------
    # RISK
    # --------------------------------------------------

    risk_score = calculate_risk_score(
        ml_prediction=ml_prediction,
        anomaly_score=anomaly_score,
        rule_anomaly=rule_anomaly,
        rule_anomaly_type=rule_anomaly_type,
        anomaly_floor=anomaly_floor
    )

    # --------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------

    confidence = calculate_confidence(
        ml_prediction=ml_prediction,
        anomaly_score=anomaly_score,
        rule_anomaly=rule_anomaly,
        rule_anomaly_type=rule_anomaly_type,
        anomaly_floor=anomaly_floor
    )

    # --------------------------------------------------
    # EXPLANATION
    # --------------------------------------------------

    explanation = generate_explanation(
        ml_prediction=ml_prediction,
        anomaly_score=anomaly_score,
        rule_anomaly=rule_anomaly,
        rule_anomaly_type=rule_anomaly_type,
        rule_feature=rule_feature,
        rule_reason=rule_reason
    )

    # --------------------------------------------------
    # SEVERITY
    # --------------------------------------------------

    severity = calculate_severity(risk_score)

    # --------------------------------------------------
    # OVERALL HEALTH
    # --------------------------------------------------

    if previous_health is None:
        previous_health = 100

    sensor_health = update_overall_health(
        previous_health=previous_health,
        ml_prediction=ml_prediction,
        rule_anomaly=rule_anomaly,
        rule_anomaly_type=rule_anomaly_type
    )

    # --------------------------------------------------
    # FEATURE HEALTH
    # --------------------------------------------------

    if feature_health is None:

        feature_health = {
            feature: 100
            for feature in FEATURES
        }

    feature_health = update_feature_health(
        health=feature_health,
        rule_anomaly=rule_anomaly,
        rule_anomaly_type=rule_anomaly_type,
        rule_feature=rule_feature
    )

    # --------------------------------------------------
    # FINAL RESULT
    # --------------------------------------------------

    return {
        "risk_score": risk_score,
        "confidence": confidence,
        "severity": severity,
        "explanation": explanation,
        "sensor_health": sensor_health,
        "feature_health": feature_health.copy()
    }


def process_dataframe(df):
    """
    Process the complete M2 + M3 dataframe.

    Returns:
        A new dataframe containing all original columns
        plus M4 outputs.
    """

    results = []

    # Overall station health
    overall_health = 100

    # Individual feature health
    feature_health = {
        feature: 100
        for feature in FEATURES
    }

    # Process every row
    for _, row in df.iterrows():

        result = process_row(
            row=row,
            previous_health=overall_health,
            feature_health=feature_health
        )

        # Update health for next reading
        overall_health = result["sensor_health"]

        feature_health = result["feature_health"]

        results.append(result)

    # --------------------------------------------------
    # ADD M4 COLUMNS
    # --------------------------------------------------

    result_df = df.copy()

    result_df["risk_score"] = [
        result["risk_score"]
        for result in results
    ]

    result_df["confidence"] = [
        result["confidence"]
        for result in results
    ]

    result_df["severity"] = [
        result["severity"]
        for result in results
    ]

    result_df["explanation"] = [
        result["explanation"]
        for result in results
    ]

    result_df["sensor_health"] = [
        result["sensor_health"]
        for result in results
    ]

    result_df["feature_health"] = [
        result["feature_health"]
        for result in results
    ]

    return result_df