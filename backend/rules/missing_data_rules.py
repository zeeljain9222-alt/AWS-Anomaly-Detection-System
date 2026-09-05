import pandas as pd


def detect_missing_values(row):
    """
    Detect missing weather sensor values in one weather record.

    Returns:
        dict: Result of the missing-data check.
    """

    weather_columns = [
        "temperature",
        "humidity",
        "pressure",
        "wind_speed",
        "rainfall",
    ]

    missing_features = []

    for feature in weather_columns:
        if pd.isna(row.get(feature)):
            missing_features.append(feature)

    if missing_features:
        return {
            "anomaly": True,
            "anomaly_type": "MISSING_DATA",
            "feature": missing_features,
            "reason": f"Missing weather values detected: {missing_features}",
        }

    return {
        "anomaly": False,
        "anomaly_type": "NORMAL",
        "feature": None,
        "reason": "No missing weather values detected",
    }

#timestamp gap
def detect_timestamp_gap(
    previous_timestamp,
    current_timestamp,
    expected_interval_minutes=10
):
    """
    Detect whether there is a gap between two weather readings.

    Args:
        previous_timestamp: Timestamp of the previous reading.
        current_timestamp: Timestamp of the current reading.
        expected_interval_minutes: Expected time between readings.

    Returns:
        dict: Result of the timestamp gap check.
    """

    previous_timestamp = pd.to_datetime(previous_timestamp)
    current_timestamp = pd.to_datetime(current_timestamp)

    actual_gap_minutes = (
        current_timestamp - previous_timestamp
    ).total_seconds() / 60

    if actual_gap_minutes > expected_interval_minutes:
        return {
            "anomaly": True,
            "anomaly_type": "MISSING_DATA",
            "feature": "timestamp",
            "value": actual_gap_minutes,
            "reason": (
                f"Timestamp gap detected. Expected "
                f"{expected_interval_minutes} minute(s), but "
                f"{actual_gap_minutes} minute(s) passed."
            ),
        }

    return {
        "anomaly": False,
        "anomaly_type": "NORMAL",
        "feature": None,
        "value": actual_gap_minutes,
        "reason": "No timestamp gap detected",
    }