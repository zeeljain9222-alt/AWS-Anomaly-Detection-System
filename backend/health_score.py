"""
M4 - Station and Feature Health

Health is maintained separately
for every AWS station.
"""

from typing import Optional


# Weather features
FEATURES = [
    "temperature",
    "humidity",
    "pressure",
    "wind_speed",
    "rainfall",
]


# Health penalty for different problems
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


def update_health(
    previous_health: float,
    ml_anomaly: bool,
    rule_anomaly: bool,
    rule_anomaly_type: Optional[str]
):
    """
    Update health score.

    Health is always between 0 and 100.
    """

    penalty = 0

    # ML anomaly
    if ml_anomaly:

        penalty += HEALTH_PENALTY["ML_ANOMALY"]

    # Rule anomaly
    if rule_anomaly and rule_anomaly_type:

        rules = [
            rule.strip().upper()
            for rule in str(rule_anomaly_type).split(",")
            if rule.strip()
            and rule.strip().upper() != "NORMAL"
        ]

        penalties = [
            HEALTH_PENALTY.get(rule, 4)
            for rule in rules
        ]

        if penalties:

            # Use strongest penalty
            penalty += max(penalties)

    # Normal reading → slight recovery
    if penalty == 0:

        new_health = (
            previous_health
            + HEALTH_RECOVERY
        )

    else:

        new_health = (
            previous_health
            - penalty
        )

    # Keep between 0 and 100
    return round(
        max(0, min(100, new_health)),
        2
    )