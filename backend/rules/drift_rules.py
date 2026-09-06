from config import DRIFT_CONFIG


def detect_drift(values, feature):

    if feature not in DRIFT_CONFIG:

        return {
            "anomaly": False,
            "anomaly_type": "NORMAL",
            "feature": feature,
            "value": values[-1] if values else None,
            "reason": f"No drift configuration for {feature}",
        }

    config = DRIFT_CONFIG[feature]

    baseline_window = config["baseline_window"]
    recent_window = config["recent_window"]
    threshold = config["threshold"]

    required_values = baseline_window + recent_window

    if len(values) < required_values:

        return {
            "anomaly": False,
            "anomaly_type": "NORMAL",
            "feature": feature,
            "value": values[-1] if values else None,
            "reason": (
                f"Not enough readings for drift detection. "
                f"Need at least {required_values} readings."
            ),
        }

    baseline_values = values[:baseline_window]
    recent_values = values[-recent_window:]

    baseline_average = sum(baseline_values) / len(baseline_values)
    recent_average = sum(recent_values) / len(recent_values)

    difference = abs(recent_average - baseline_average)

    if difference > threshold:

        return {
            "anomaly": True,
            "anomaly_type": "DRIFT",
            "feature": feature,
            "value": recent_average,
            "position": len(values) - 1,
            "reason": (
                f"Drift detected in {feature}. "
                f"Baseline average: {baseline_average:.2f}, "
                f"recent average: {recent_average:.2f}, "
                f"difference: {difference:.2f}, "
                f"threshold: {threshold:.2f}."
            ),
        }

    return {
        "anomaly": False,
        "anomaly_type": "NORMAL",
        "feature": feature,
        "value": recent_average,
        "reason": f"No drift detected in {feature}",
    }