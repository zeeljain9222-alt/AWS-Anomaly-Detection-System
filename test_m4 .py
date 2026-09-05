"""
M4 - Test Suite

Tests:
1. Normal reading
2. ML anomaly
3. SPIKE
4. FROZEN_VALUE
5. DRIFT
6. MISSING_DATA
7. TIMESTAMP_GAP
8. ML + Rule anomaly
9. Multiple rules
10. Missing anomaly score
"""

from m4_processor import process_row


def create_row(
    ml_prediction=0,
    anomaly_score=0.10,
    rule_anomaly=False,
    rule_anomaly_type="NORMAL",
    rule_feature=None,
    rule_reason=None
):
    return {
        "ml_prediction": ml_prediction,
        "anomaly_score": anomaly_score,
        "rule_anomaly": rule_anomaly,
        "rule_anomaly_type": rule_anomaly_type,
        "rule_feature": rule_feature,
        "rule_reason": rule_reason
    }


def run_test(name, row):
    result = process_row(row)

    print(f"\n{name}")
    print("-" * 50)
    print("Risk       :", result["risk_score"])
    print("Confidence :", result["confidence"])
    print("Severity   :", result["severity"])
    print("Explanation:", result["explanation"])
    print("Health     :", result["sensor_health"])
    print("Features   :", result["feature_health"])


# --------------------------------------------------
# 1. NORMAL READING
# --------------------------------------------------

run_test(
    "TEST 1 - Normal Reading",
    create_row(
        ml_prediction=0,
        anomaly_score=0.10,
        rule_anomaly=False,
        rule_anomaly_type="NORMAL"
    )
)


# --------------------------------------------------
# 2. ML-ONLY ANOMALY
# --------------------------------------------------

run_test(
    "TEST 2 - ML Only Anomaly",
    create_row(
        ml_prediction=1,
        anomaly_score=-0.02,
        rule_anomaly=False,
        rule_anomaly_type="NORMAL"
    )
)


# --------------------------------------------------
# 3. SPIKE
# --------------------------------------------------

run_test(
    "TEST 3 - Spike",
    create_row(
        ml_prediction=0,
        anomaly_score=0.10,
        rule_anomaly=True,
        rule_anomaly_type="SPIKE",
        rule_feature="temperature",
        rule_reason="Temperature increased sharply between consecutive readings."
    )
)


# --------------------------------------------------
# 4. FROZEN VALUE
# --------------------------------------------------

run_test(
    "TEST 4 - Frozen Value",
    create_row(
        ml_prediction=0,
        anomaly_score=0.10,
        rule_anomaly=True,
        rule_anomaly_type="FROZEN_VALUE",
        rule_feature="rainfall",
        rule_reason="Rainfall remained unchanged across consecutive readings."
    )
)


# --------------------------------------------------
# 5. DRIFT
# --------------------------------------------------

run_test(
    "TEST 5 - Drift",
    create_row(
        ml_prediction=0,
        anomaly_score=0.10,
        rule_anomaly=True,
        rule_anomaly_type="DRIFT",
        rule_feature="temperature",
        rule_reason="Temperature differs significantly from its baseline."
    )
)


# --------------------------------------------------
# 6. MISSING DATA
# --------------------------------------------------

run_test(
    "TEST 6 - Missing Data",
    create_row(
        ml_prediction=0,
        anomaly_score=0.10,
        rule_anomaly=True,
        rule_anomaly_type="MISSING_DATA",
        rule_feature="humidity",
        rule_reason="Humidity observation is missing."
    )
)


# --------------------------------------------------
# 7. TIMESTAMP GAP
# --------------------------------------------------

run_test(
    "TEST 7 - Timestamp Gap",
    create_row(
        ml_prediction=0,
        anomaly_score=0.10,
        rule_anomaly=True,
        rule_anomaly_type="TIMESTAMP_GAP",
        rule_feature="timestamp",
        rule_reason="Expected timestamp sequence contains a gap."
    )
)


# --------------------------------------------------
# 8. ML + RULE ANOMALY
# --------------------------------------------------

run_test(
    "TEST 8 - ML + Rule Anomaly",
    create_row(
        ml_prediction=1,
        anomaly_score=-0.04,
        rule_anomaly=True,
        rule_anomaly_type="SPIKE",
        rule_feature="temperature",
        rule_reason="Temperature increased sharply."
    )
)


# --------------------------------------------------
# 9. MULTIPLE RULES
# --------------------------------------------------

run_test(
    "TEST 9 - Multiple Rules",
    create_row(
        ml_prediction=0,
        anomaly_score=0.10,
        rule_anomaly=True,
        rule_anomaly_type="SPIKE,DRIFT",
        rule_feature="temperature",
        rule_reason="Temperature shows both a sudden spike and significant drift."
    )
)


# --------------------------------------------------
# 10. MISSING ANOMALY SCORE
# --------------------------------------------------

run_test(
    "TEST 10 - Missing Anomaly Score",
    create_row(
        ml_prediction=1,
        anomaly_score=None,
        rule_anomaly=False,
        rule_anomaly_type="NORMAL"
    )
)


print("\n" + "=" * 50)
print("M4 TESTING COMPLETED")
print("=" * 50)