"""
M4 - Main Processor

Input:
    M2 + M3 integrated CSV

Adds:
    risk_score
    confidence
    severity
    explanation
    station_health
    feature_health

Health is maintained separately
for each AWS station.
"""

import json
import pandas as pd

from risk_score import (
    calculate_risk_score,
    is_ml_anomaly
)

from explanations import (
    generate_explanation
)

from health_score import (
    update_health,
    FEATURES,
    HEALTH_RECOVERY
)


# Confidence values for rule-based detections
RULE_CONFIDENCE = {

    "MISSING_DATA": 0.98,

    "TIMESTAMP_GAP": 0.95,

    "SPIKE": 0.90,

    "FROZEN_VALUE": 0.95,

    "DRIFT": 0.90,
}


def calculate_confidence(
    ml_prediction,
    anomaly_score,
    rule_anomaly,
    rule_anomaly_type,
    ml_status=None,
    anomaly_floor=-0.20
):
    """
    Calculate confidence between 0 and 1.
    """

    # -----------------------------
    # RULE CONFIDENCE
    # -----------------------------

    if rule_anomaly and rule_anomaly_type:

        rules = [

            rule.strip().upper()

            for rule in str(
                rule_anomaly_type
            ).split(",")

            if rule.strip()
            and rule.strip().upper() != "NORMAL"
        ]

        values = [

            RULE_CONFIDENCE.get(
                rule,
                0.85
            )

            for rule in rules
        ]

        if values:

            return max(values)

    # -----------------------------
    # ML CONFIDENCE
    # -----------------------------

    if is_ml_anomaly(
        ml_prediction,
        ml_status
    ):

        if anomaly_score is None:

            return 0.70

        strength = (
            abs(float(anomaly_score))
            / abs(anomaly_floor)
        )

        strength = max(
            0.0,
            min(strength, 1.0)
        )

        confidence = (
            0.70
            + strength * 0.29
        )

        return round(
            confidence,
            2
        )

    # -----------------------------
    # NORMAL
    # -----------------------------

    return 1.0


def calculate_severity(risk_score):
    """
    Convert risk score into severity.
    """

    if risk_score <= 19:

        return "LOW"

    elif risk_score <= 39:

        return "MEDIUM"

    elif risk_score <= 59:

        return "HIGH"

    elif risk_score <= 79:

        return "VERY HIGH"

    else:

        return "CRITICAL"


def process_row(
    row,
    previous_station_health=100.0,
    previous_feature_health=None,
    anomaly_floor=-0.20
):
    """
    Process one weather record.
    """

    # -----------------------------
    # READ M2 DATA
    # -----------------------------

    ml_prediction = row["ml_prediction"]

    ml_status = row.get(
        "ml_status"
    )

    try:

        anomaly_score = float(
            row["anomaly_score"]
        )

    except (ValueError, TypeError):

        anomaly_score = None


    # -----------------------------
    # READ M3 DATA
    # -----------------------------

    rule_value = row["rule_anomaly"]

    if isinstance(
        rule_value,
        str
    ):

        rule_anomaly = (
            rule_value
            .strip()
            .lower()
            == "true"
        )

    else:

        rule_anomaly = bool(
            rule_value
        )


    rule_anomaly_type = row.get(
        "rule_anomaly_type"
    )

    rule_feature = row.get(
        "rule_feature"
    )

    rule_reason = row.get(
        "rule_reason"
    )


    # -----------------------------
    # DETERMINE ML ANOMALY
    # -----------------------------

    ml_anomaly = is_ml_anomaly(
        ml_prediction,
        ml_status
    )


    # -----------------------------
    # RISK
    # -----------------------------

    risk_score = calculate_risk_score(

        ml_prediction,

        anomaly_score,

        rule_anomaly,

        rule_anomaly_type,

        ml_status,

        anomaly_floor
    )


    # -----------------------------
    # CONFIDENCE
    # -----------------------------

    confidence = calculate_confidence(

        ml_prediction,

        anomaly_score,

        rule_anomaly,

        rule_anomaly_type,

        ml_status,

        anomaly_floor
    )


    # -----------------------------
    # EXPLANATION
    # -----------------------------

    explanation = generate_explanation(

        ml_prediction,

        anomaly_score,

        rule_anomaly,

        rule_anomaly_type,

        rule_feature,

        rule_reason,

        ml_status
    )


    # -----------------------------
    # SEVERITY
    # -----------------------------

    severity = calculate_severity(
        risk_score
    )


    # -----------------------------
    # FEATURE HEALTH INITIALIZATION
    # -----------------------------

    if previous_feature_health is None:

        previous_feature_health = {

            feature: 100.0

            for feature in FEATURES
        }

    else:

        previous_feature_health = dict(
            previous_feature_health
        )


    # -----------------------------
    # STATION HEALTH
    # -----------------------------

    station_health = update_health(

        previous_station_health,

        ml_anomaly,

        rule_anomaly,

        rule_anomaly_type
    )


    # -----------------------------
    # FEATURE HEALTH
    # -----------------------------

    if (
        rule_anomaly
        and rule_feature
    ):

        feature_name = (
            str(rule_feature)
            .strip()
            .lower()
        )

        if feature_name in previous_feature_health:

            previous_feature_health[
                feature_name
            ] = update_health(

                previous_feature_health[
                    feature_name
                ],

                ml_anomaly=False,

                rule_anomaly=True,

                rule_anomaly_type=
                    rule_anomaly_type
            )


    # -----------------------------
    # NORMAL FEATURE RECOVERY
    # -----------------------------

    if not rule_anomaly:

        for feature in FEATURES:

            previous_feature_health[
                feature
            ] = min(

                100.0,

                round(

                    previous_feature_health[
                        feature
                    ]
                    + HEALTH_RECOVERY,

                    2
                )
            )


    # -----------------------------
    # RETURN RESULT
    # -----------------------------

    return {

        "risk_score":
            risk_score,

        "confidence":
            confidence,

        "severity":
            severity,

        "explanation":
            explanation,

        "station_health":
            station_health,

        "feature_health":
            previous_feature_health,
    }


def process_dataframe(df):
    """
    Process complete M2 + M3 dataset.

    Health is maintained independently
    for every station.
    """

    # Make sure each station's
    # readings are processed in time order.

    df = df.sort_values(
        [
            "station_id",
            "timestamp"
        ]
    ).copy()


    results = []

    # Store health separately
    # for every station.

    station_health = {}

    feature_health = {}


    # -----------------------------
    # PROCESS EACH ROW
    # -----------------------------

    for _, row in df.iterrows():

        station_id = str(
            row["station_id"]
        )


        # First record for station
        if station_id not in station_health:

            station_health[
                station_id
            ] = 100.0


        if station_id not in feature_health:

            feature_health[
                station_id
            ] = {

                feature: 100.0

                for feature in FEATURES
            }


        # Process record

        result = process_row(

            row,

            previous_station_health=
                station_health[
                    station_id
                ],

            previous_feature_health=
                feature_health[
                    station_id
                ]
        )


        # Save updated health

        station_health[
            station_id
        ] = result[
            "station_health"
        ]


        feature_health[
            station_id
        ] = result[
            "feature_health"
        ]


        results.append(
            result
        )


    # -----------------------------
    # CREATE OUTPUT DATAFRAME
    # -----------------------------

    result_df = df.copy()


    result_df[
        "risk_score"
    ] = [

        result[
            "risk_score"
        ]

        for result in results
    ]


    result_df[
        "confidence"
    ] = [

        result[
            "confidence"
        ]

        for result in results
    ]


    result_df[
        "severity"
    ] = [

        result[
            "severity"
        ]

        for result in results
    ]


    result_df[
        "explanation"
    ] = [

        result[
            "explanation"
        ]

        for result in results
    ]


    result_df[
        "station_health"
    ] = [

        result[
            "station_health"
        ]

        for result in results
    ]


    # Convert dictionary to JSON
    # so CSV can store it.

    result_df[
        "feature_health"
    ] = [

        json.dumps(
            result[
                "feature_health"
            ],
            sort_keys=True
        )

        for result in results
    ]


    return result_df