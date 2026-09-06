def detect_frozen_value(
    values,
    minimum_repetitions=5,
    feature=None
):
    """
    Detect whether a sensor remains stuck at the same value.
    """

    if len(values) < minimum_repetitions:
        return {
            "anomaly": False,
            "anomaly_type": "NORMAL",
            "feature": feature,
            "value": None,
            "reason": "Not enough readings to detect a frozen value",
        }

    # Rainfall = 0 for many readings is normal
    if feature == "rainfall":
        return {
            "anomaly": False,
            "anomaly_type": "NORMAL",
            "feature": feature,
            "value": None,
            "reason": "Rainfall values are not checked for frozen readings",
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
                "feature": feature,
                "value": values[i],
                "position": i,
                "reason": (
                    f"{feature} remained unchanged at "
                    f"{values[i]} for "
                    f"{consecutive_count} consecutive readings"
                ),
            }

    return {
        "anomaly": False,
        "anomaly_type": "NORMAL",
        "feature": feature,
        "value": None,
        "reason": "No frozen value detected",
    }