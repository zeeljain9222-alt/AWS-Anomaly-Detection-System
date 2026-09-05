"""
M4 - Explanation Generator

Converts M2/M3 detection information
into human-readable explanations.
"""

from typing import Optional


def generate_explanation(
    ml_prediction: int,
    anomaly_score: Optional[float],
    rule_anomaly: bool,
    rule_anomaly_type: Optional[str],
    rule_feature: Optional[str],
    rule_reason: Optional[str]
) -> str:
    """
    Generate an explanation for the detected condition.
    """

    # --------------------------------------------------
    # RULE-BASED ANOMALY
    # --------------------------------------------------

    if rule_anomaly:

        rules = [
            rule.strip().upper()
            for rule in str(rule_anomaly_type).split(",")
            if rule.strip()
        ]

        # Ignore NORMAL because it is not an anomaly
        rules = [
            rule for rule in rules
            if rule != "NORMAL"
        ]

        rule_name = ", ".join(
            rule.replace("_", " ").title()
            for rule in rules
        )

        # M3 already provides a reason.
        # Preserve it instead of recreating it.
        if rule_reason and str(rule_reason).strip():

            return (
                f"{rule_name} detected for "
                f"{rule_feature or 'the sensor'}. "
                f"{str(rule_reason).strip()}"
            )

        # Fallback explanations
        explanations = []

        for rule in rules:

            if rule == "MISSING_DATA":
                explanations.append(
                    f"Missing observation detected for "
                    f"{rule_feature or 'the sensor'}."
                )

            elif rule == "TIMESTAMP_GAP":
                explanations.append(
                    "A gap was detected in the expected "
                    "timestamp sequence."
                )

            elif rule == "SPIKE":
                explanations.append(
                    f"A sudden spike was detected in "
                    f"{rule_feature or 'the measurement'}."
                )

            elif rule == "FROZEN_VALUE":
                explanations.append(
                    f"The {rule_feature or 'sensor'} value "
                    "remained unchanged across consecutive "
                    "readings and may indicate a stuck sensor."
                )

            elif rule == "DRIFT":
                explanations.append(
                    f"The {rule_feature or 'sensor'} shows "
                    "significant drift from its baseline."
                )

        return " ".join(explanations)

    # --------------------------------------------------
    # ML ANOMALY
    # --------------------------------------------------

    if ml_prediction == 1:

        if anomaly_score is not None:

            return (
                "Isolation Forest detected an unusual "
                f"weather pattern "
                f"(anomaly score: {float(anomaly_score):.4f})."
            )

        return (
            "Isolation Forest detected an unusual "
            "weather pattern."
        )

    # --------------------------------------------------
    # NORMAL
    # --------------------------------------------------

    return "Weather reading is normal."