def detect_frozen_value(values, minimum_repetitions=5):
    """
    Detect whether a sensor value remains exactly the same
    for too many consecutive readings.

    Args:
        values: List of sensor readings.
        minimum_repetitions: Number of identical consecutive
                             values required to trigger the rule.

    Returns:
        dict: Result of the frozen-value check.
    """

    if len(values) < minimum_repetitions:
        return {
            "anomaly": False,
            "anomaly_type": "NORMAL",
            "feature": None,
            "value": None,
            "reason": "Not enough readings to detect a frozen value",
        }

    consecutive_count = 1

    for i in range(1, len(values)):

        if values[i] == values[i - 1]:
            consecutive_count += 1
        else:
            consecutive_count = 1

        if consecutive_count >= minimum_repetitions:
            return {
                "anomaly": True,
                "anomaly_type": "FROZEN_VALUE",
                "feature": None,
                "value": values[i],
                "position": i,
                "reason": (
                    f"Value {values[i]} remained unchanged for "
                    f"{consecutive_count} consecutive readings"
                ),
            }

    return {
        "anomaly": False,
        "anomaly_type": "NORMAL",
        "feature": None,
        "value": None,
        "reason": "No frozen value detected",
    }