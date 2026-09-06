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


def create_anomaly_result(result, timestamp=None, station_id=None):
    """
    Convert a rule result dictionary into
    the standard AnomalyResult format.
    """

    return AnomalyResult(
        anomaly=result.get("anomaly", False),
        anomaly_type=result.get("anomaly_type", "NORMAL"),
        feature=result.get("feature"),
        value=result.get("value"),
        timestamp=timestamp,
        reason=result.get("reason", ""),
        station_id=station_id,
    )


def analyze_single_station(data, station_id):
    """
    Run all M3 anomaly detection rules
    for one AWS station only.
    """

    results = []

    # Sort readings by timestamp
    data = data.sort_values("timestamp").reset_index(drop=True)

    # --------------------------------------------------
    # 1. Missing sensor values
    # --------------------------------------------------

    for _, row in data.iterrows():

        result = detect_missing_values(row)

        if result["anomaly"]:

            anomaly_result = create_anomaly_result(
                result,
                timestamp=row.get("timestamp"),
                station_id=station_id,
            )

            results.append(anomaly_result)

    # --------------------------------------------------
    # 2. Timestamp gap detection
    # --------------------------------------------------

    if len(data) > 1:

        for i in range(1, len(data)):

            result = detect_timestamp_gap(
                data["timestamp"].iloc[i - 1],
                data["timestamp"].iloc[i],
                expected_interval_minutes=60
            )

            if result["anomaly"]:

                anomaly_result = create_anomaly_result(
                    result,
                    timestamp=data["timestamp"].iloc[i],
                    station_id=station_id,
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
                    station_id=station_id,
                )

                results.append(anomaly_result)

    # --------------------------------------------------
    # 4. Frozen value detection
    # --------------------------------------------------

    for feature in WEATHER_FEATURES:

        if feature not in data.columns:
            continue

        values = data[feature].dropna().tolist()
        original_indices = data.index[
            data[feature].notna()
        ].tolist()

        result = detect_frozen_value(
    values,
    feature=feature
)

        if result["anomaly"]:

            result["feature"] = feature

            position = result.get("position")

            if (
                position is not None
                and position < len(original_indices)
            ):
                original_index = original_indices[position]

                timestamp = data.loc[
                    original_index,
                    "timestamp"
                ]
            else:
                timestamp = None

            anomaly_result = create_anomaly_result(
                result,
                timestamp=timestamp,
                station_id=station_id,
            )

            results.append(anomaly_result)

    # --------------------------------------------------
    # 5. Drift detection
    # --------------------------------------------------

    for feature in WEATHER_FEATURES:

        if feature not in data.columns:
            continue

        values = data[feature].dropna().tolist()

        result = detect_drift(
            values=values,
            feature=feature,
        )

        if result["anomaly"]:

            anomaly_result = create_anomaly_result(
                result,
                timestamp=data["timestamp"].iloc[-1],
                station_id=station_id,
            )

            results.append(anomaly_result)

    return results


def analyze_weather_data(df):
    """
    Run M3 anomaly detection rules.

    If multiple AWS stations are present,
    each station is analyzed separately.
    """

    data = df.copy()

    # Convert timestamp to datetime
    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        format="mixed",
        dayfirst=True
    )

    results = []

    # --------------------------------------------------
    # Analyze each AWS station separately
    # --------------------------------------------------

    if "station_id" in data.columns:

        for station_id, station_data in data.groupby(
            "station_id"
        ):

            station_results = analyze_single_station(
                station_data.copy(),
                station_id
            )

            results.extend(station_results)

    else:

        # If station_id is not available,
        # analyze the complete dataset
        results = analyze_single_station(
            data,
            station_id=None
        )

    return results


def analyze_weather_csv(csv_path):
    """
    Load CSV and run the M3 Rule Engine.
    """

    data = pd.read_csv(csv_path)

    return analyze_weather_data(data)


def integrate_m2_m3(df):
    """
    Combine M2 ML results with
    M3 rule-based results.
    """

    data = df.copy()

    # Convert timestamp
    data["timestamp"] = pd.to_datetime(
        data["timestamp"],
        format="mixed",
        dayfirst=True
    )

    # Run M3 rules
    m3_results = analyze_weather_data(data)

    # Preserve M2 output
    integrated = data.copy()

    # Add M3 columns
    integrated["rule_anomaly"] = False
    integrated["rule_anomaly_type"] = "NORMAL"
    integrated["rule_feature"] = None
    integrated["rule_reason"] = ""

    # --------------------------------------------------
    # Add M3 results to matching station + timestamp
    # --------------------------------------------------

    for result in m3_results:

        if not result.anomaly:
            continue

        # Match both station and timestamp
        if result.station_id is not None:

            matches = (
                (integrated["station_id"] == result.station_id)
                &
                (integrated["timestamp"] == result.timestamp)
            )

        else:

            matches = (
                integrated["timestamp"]
                == result.timestamp
            )

        integrated.loc[
            matches,
            "rule_anomaly"
        ] = True

        # Add anomaly type
        existing_type = integrated.loc[
            matches,
            "rule_anomaly_type"
        ].iloc[0]

        if existing_type == "NORMAL":

            integrated.loc[
                matches,
                "rule_anomaly_type"
            ] = result.anomaly_type

        else:

            integrated.loc[
                matches,
                "rule_anomaly_type"
            ] = (
                existing_type
                + ", "
                + result.anomaly_type
            )

        # Add feature
        if result.feature is not None:

            if isinstance(result.feature, list):

                feature_value = ", ".join(
                    result.feature
                )

            else:

                feature_value = str(
                    result.feature
                )

            integrated.loc[
                matches,
                "rule_feature"
            ] = feature_value

        # Add reason
        integrated.loc[
            matches,
            "rule_reason"
        ] = result.reason

    return integrated