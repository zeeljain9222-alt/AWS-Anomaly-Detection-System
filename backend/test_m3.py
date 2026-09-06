import pandas as pd

from rule_engine import analyze_weather_data


# ==========================================
# CREATE TEST DATA
# ==========================================

data = pd.DataFrame({

    "timestamp": [
        "2025-01-01 00:00",
        "2025-01-01 01:00",
        "2025-01-01 02:00",
        "2025-01-01 03:00",
        "2025-01-01 04:00",

        # Timestamp gap here
        "2025-01-01 08:00",

        "2025-01-01 09:00",
        "2025-01-01 10:00",
        "2025-01-01 11:00",
        "2025-01-01 12:00",
    ],

    "station_id": [
        "AWS_001",
        "AWS_001",
        "AWS_001",
        "AWS_001",
        "AWS_001",
        "AWS_001",
        "AWS_001",
        "AWS_001",
        "AWS_001",
        "AWS_001",
    ],

    # Gradual increase to test DRIFT
    "temperature": [
        20,
        20,
        20,
        20,
        20,
        23,
        24,
        25,
        26,
        27
    ],

    "humidity": [
        60,
        61,
        62,
        63,
        64,
        65,
        66,
        67,
        68,
        69
    ],

    "pressure": [
        1000,
        1001,
        1000,
        1001,
        1000,
        1001,
        1000,
        1001,
        1000,
        1001
    ],

    "wind_speed": [
        5,
        6,
        5,
        6,
        5,
        6,
        5,
        6,
        5,
        6
    ],

    # Missing value here
    "rainfall": [
        0,
        0,
        None,
        0,
        0,
        0,
        0,
        0,
        0,
        0
    ]
})


# ==========================================
# RUN M3 RULE ENGINE
# ==========================================

results = analyze_weather_data(data)


print("\n========== M3 ANOMALY RESULTS ==========\n")


if not results:
    print("No anomalies detected.")

else:

    for result in results:

        print("Station:", result.station_id)
        print("Timestamp:", result.timestamp)
        print("Anomaly:", result.anomaly)
        print("Type:", result.anomaly_type)
        print("Feature:", result.feature)
        print("Value:", result.value)
        print("Reason:", result.reason)

        print("-" * 50)