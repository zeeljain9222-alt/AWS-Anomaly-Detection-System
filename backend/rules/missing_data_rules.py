import pandas as pd


WEATHER_COLUMNS = [
    "temperature",
    "humidity",
    "pressure",
    "wind_speed",
    "rainfall",
]


def detect_missing_values(row):

    missing_features = []

    for feature in WEATHER_COLUMNS:

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


def detect_timestamp_gap(
    previous_timestamp,
    current_timestamp,
    expected_interval_minutes=60
):

    previous_timestamp = pd.to_datetime(previous_timestamp)
    current_timestamp = pd.to_datetime(current_timestamp)

    actual_gap_minutes = (
        current_timestamp - previous_timestamp
    ).total_seconds() / 60

    if actual_gap_minutes > expected_interval_minutes:

        return {
            "anomaly": True,
            "anomaly_type": "TIMESTAMP_GAP",
            "feature": "timestamp",
            "value": actual_gap_minutes,
            "reason": (
                f"Timestamp gap detected. Expected "
                f"{expected_interval_minutes} minutes, but "
                f"{actual_gap_minutes} minutes passed."
            ),
        }

    return {
        "anomaly": False,
        "anomaly_type": "NORMAL",
        "feature": None,
        "value": actual_gap_minutes,
        "reason": "No timestamp gap detected",
    }