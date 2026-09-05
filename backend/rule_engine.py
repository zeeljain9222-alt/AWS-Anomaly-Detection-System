import pandas as pd

from models.anomaly_result import AnomalyResult

from rules.missing_data_rules import (
    detect_missing_values,
    detect_timestamp_gap,
)

from rules.frozen_value_rules import detect_frozen_value
from rules.spike_rules import detect_spike
from rules.drift_rules import detect_drift


WEATHER_FEATURES = [
    "temperature",
    "humidity",
    "pressure",
    "wind_speed",
    "rainfall",
]


def create_anomaly_result(result, timestamp=None):
    """
    Convert a rule result dictionary into the standard
    AnomalyResult format.
    """

    return AnomalyResult(
        anomaly=result.get("anomaly", False),
        anomaly_type=result.get("anomaly_type", "NORMAL"),
        feature=result.get("feature"),
        value=result.get("value"),
        timestamp=timestamp,
        reason=result.get("reason", ""),
    )


def analyze_weather_data(df):
    """
    Run all M3 anomaly detection rules on weather data.

    Args:
        df: Pandas DataFrame containing weather observations.

    Returns:
        list: List of detected anomalies.
    """

    results = []

    # Make a copy so the original DataFrame is not modified.
    data = df.copy()

    # Make sure timestamps are datetime values.
    if "timestamp" in data.columns:
        data["timestamp"] = pd.to_datetime(
            data["timestamp"],
            format="mixed",
            dayfirst=True
        )

    # --------------------------------------------------
    # 1. Missing sensor values
    # --------------------------------------------------

    for index, row in data.iterrows():

        result = detect_missing_values(row)

        if result["anomaly"]:

            anomaly_result = create_anomaly_result(
                result,
                timestamp=row.get("timestamp"),
            )

            results.append(anomaly_result)

    # --------------------------------------------------
    # 2. Timestamp gaps
    # --------------------------------------------------

    if "timestamp" in data.columns and len(data) > 1:

        timestamps = data["timestamp"].reset_index(drop=True)

        for i in range(1, len(timestamps)):

            result = detect_timestamp_gap(
                timestamps.iloc[i - 1],
                timestamps.iloc[i],
            )

            if result["anomaly"]:

                anomaly_result = create_anomaly_result(
                    result,
                    timestamp=timestamps.iloc[i],
                )

                results.append(anomaly_result)

    # --------------------------------------------------
    # 3. Spike detection
    # --------------------------------------------------

    for feature in WEATHER_FEATURES:

        if feature not in data.columns:
            continue

        for i in range(1, len(data)):

            previous_value = data[feature].iloc[i - 1]
            current_value = data[feature].iloc[i]

            # Skip missing values.
            if pd.isna(previous_value) or pd.isna(current_value):
                continue

            result = detect_spike(
                previous_value=previous_value,
                current_value=current_value,
                feature=feature,
            )

            if result["anomaly"]:

                anomaly_result = create_anomaly_result(
                    result,
                    timestamp=data["timestamp"].iloc[i],
                )

                results.append(anomaly_result)

    # --------------------------------------------------
    # 4. Frozen value detection
    # --------------------------------------------------

    for feature in WEATHER_FEATURES:

        if feature not in data.columns:
            continue

        values = data[feature].dropna().tolist()
        original_indices = data.index[data[feature].notna()].tolist()

        result = detect_frozen_value(values)

        if result["anomaly"]:
            result["feature"] = feature

            position = result.get("position")

            if position is not None and position < len(original_indices):
                original_index = original_indices[position]
                timestamp = data.loc[original_index, "timestamp"]
            else:
                timestamp = None

            anomaly_result = create_anomaly_result(
                result,
                timestamp=timestamp,
            )

            results.append(anomaly_result)

    # --------------------------------------------------
    # 5. Drift detection
    # --------------------------------------------------

    for feature in WEATHER_FEATURES:

        if feature not in data.columns:
            continue

        values = data[feature].dropna().tolist()
        original_indices = data.index[data[feature].notna()].tolist()

        result = detect_drift(
            values=values,
            feature=feature,
        )

        if result["anomaly"]:

            position = result.get("position")

            if position is not None and position < len(original_indices):
                original_index = original_indices[position]
                timestamp = data.loc[original_index, "timestamp"]
            else:
                timestamp = None

            anomaly_result = create_anomaly_result(
                result,
                timestamp=timestamp,
            )

            results.append(anomaly_result)

    return results

def analyze_weather_csv(csv_path):
    """
    Load M2 output CSV and run the M3 Rule Engine.
    """

    data = pd.read_csv(csv_path)

    return analyze_weather_data(data)

def integrate_m2_m3(df):
    """
    Combine M2 ML results with M3 rule-based results.

    M2 columns are preserved.
    M3 can report multiple rule anomalies for the same timestamp.
    """

    data = df.copy()

    # Parse timestamps
    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        format="mixed",
        dayfirst=True
    )

    # Run M3 rules
    m3_results = analyze_weather_data(data)

    # Preserve all M2 columns
    integrated = data.copy()

    # M3 output columns
    integrated["rule_anomaly"] = False
    integrated["rule_anomaly_type"] = "NORMAL"
    integrated["rule_feature"] = None
    integrated["rule_reason"] = ""

    # Group multiple M3 results by timestamp
    grouped_results = {}

    for result in m3_results:

        timestamp = result.timestamp

        if timestamp not in grouped_results:
            grouped_results[timestamp] = []

        grouped_results[timestamp].append(result)

    # Add M3 results to corresponding rows
    for timestamp, results in grouped_results.items():

        matches = integrated["timestamp"] == timestamp

        anomaly_types = []
        features = []
        reasons = []

        for result in results:

            if result.anomaly:

                anomaly_types.append(result.anomaly_type)

                if result.feature is not None:
                    if isinstance(result.feature, list):
                        features.extend(result.feature)
                    else:
                        features.append(result.feature)

                if result.reason:
                    reasons.append(result.reason)

        if anomaly_types:

            integrated.loc[matches, "rule_anomaly"] = True

            integrated.loc[matches, "rule_anomaly_type"] = (
                ", ".join(dict.fromkeys(anomaly_types))
            )

            integrated.loc[matches, "rule_feature"] = (
                ", ".join(dict.fromkeys(features))
                if features
                else None
            )

            integrated.loc[matches, "rule_reason"] = (
                " | ".join(dict.fromkeys(reasons))
            )

    return integrated