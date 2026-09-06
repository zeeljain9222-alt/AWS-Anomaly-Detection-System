from config import SPIKE_THRESHOLDS


def detect_spike(previous_value, current_value, feature):

    if feature not in SPIKE_THRESHOLDS:
        return {
            "anomaly": False,
            "anomaly_type": "NORMAL",
            "feature": feature,
            "value": current_value,
            "reason": f"No spike threshold configured for {feature}",
        }

    threshold = SPIKE_THRESHOLDS[feature]

    change = abs(current_value - previous_value)

    if change > threshold:

        return {
            "anomaly": True,
            "anomaly_type": "SPIKE",
            "feature": feature,
            "value": current_value,
            "reason": (
                f"Sudden change detected in {feature}. "
                f"Value changed by {change:.2f}, "
                f"which is greater than the threshold {threshold}."
            ),
        }

    return {
        "anomaly": False,
        "anomaly_type": "NORMAL",
        "feature": feature,
        "value": current_value,
        "reason": f"No spike detected in {feature}",
    }