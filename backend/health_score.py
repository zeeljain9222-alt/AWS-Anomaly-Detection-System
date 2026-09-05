"""
M4 - Sensor Health Score

Tracks:
    - Overall station health
    - Individual weather feature health
"""

from typing import Optional


FEATURES = [
    "temperature",
    "humidity",
    "pressure",
    "wind_speed",
    "rainfall"
]


# Health penalty for different anomaly types
HEALTH_PENALTY = {
    "ML_ANOMALY": 2,
    "TIMESTAMP_GAP": 3,
    "SPIKE": 5,
    "DRIFT": 6,
    "FROZEN_VALUE": 8,
    "MISSING_DATA": 8,
}


# Small recovery when readings are normal
HEALTH_RECOVERY = 0.5


def calculate_health_change(
    ml_prediction: int,
    rule_anomaly: bool,
    rule_anomaly_type: Optional[str]
) -> float:
    """
    Calculate how much health should change.
    """

    penalty = 0

    # ML anomaly
    if ml_prediction == 1:
        penalty += HEALTH_PENALTY["ML_ANOMALY"]

    # Rule anomaly
    if rule_anomaly and rule_anomaly_type:

        rules = [
            rule.strip().upper()
            for rule in str(rule_anomaly_type).split(",")
            if rule.strip()
        ]

        rule_penalties = [
            HEALTH_PENALTY.get(rule, 4)
            for rule in rules
            if rule != "NORMAL"
        ]

        if rule_penalties:
            # Use the strongest rule
            penalty += max(rule_penalties)

    # Normal reading → gradual recovery
    if penalty == 0:
        return HEALTH_RECOVERY

    return -penalty


def update_overall_health(
    previous_health: float,
    ml_prediction: int,
    rule_anomaly: bool,
    rule_anomaly_type: Optional[str]
) -> float:
    """
    Update overall station health.
    """

    change = calculate_health_change(
        ml_prediction,
        rule_anomaly,
        rule_anomaly_type
    )

    new_health = previous_health + change

    return round(
        max(0, min(100, new_health)),
        2
    )


def update_feature_health(
    health: dict,
    rule_anomaly: bool,
    rule_anomaly_type: Optional[str],
    rule_feature: Optional[str]
) -> dict:
    """
    Update health of the specific feature affected
    by the M3 rule.
    """

    if not rule_anomaly:
        return health

    if not rule_feature:
        return health

    feature = str(rule_feature).strip().lower()

    if feature not in health:
        return health

    change = calculate_health_change(
        ml_prediction=0,
        rule_anomaly=True,
        rule_anomaly_type=rule_anomaly_type
    )

    health[feature] = round(
        max(0, min(100, health[feature] + change)),
        2
    )

    return health