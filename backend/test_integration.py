import pandas as pd
import joblib

from rule_engine import integrate_m2_m3


# ==========================================
# 1. LOAD DATASET
# ==========================================

df = pd.read_csv("../data/merged_weather.csv")

print("Dataset loaded successfully!")
print(df.head())


# ==========================================
# 2. PREPROCESS
# ==========================================

features = [
    "temperature",
    "humidity",
    "pressure",
    "wind_speed",
    "rainfall"
]

# Convert timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Sort station-wise and timestamp-wise
df = df.sort_values(
    ["station_id", "timestamp"]
).reset_index(drop=True)


# ==========================================
# 3. LOAD M2 MODEL + SCALER
# ==========================================

model = joblib.load(
    "models/isolation_forest_model.pkl"
)

scaler = joblib.load(
    "models/scaler.pkl"
)


# ==========================================
# 4. M2 - ML ANOMALY DETECTION
# ==========================================

X = df[features]

X_scaled = scaler.transform(X)

predictions = model.predict(X_scaled)

df["ml_prediction"] = predictions

df["ml_status"] = df["ml_prediction"].map({
    1: "Normal",
    -1: "Anomaly"
})

df["anomaly_score"] = model.decision_function(
    X_scaled
)

print("\n========== M2 RESULTS ==========")

print(
    df[
        [
            "timestamp",
            "station_id",
            "temperature",
            "humidity",
            "pressure",
            "wind_speed",
            "rainfall",
            "ml_status",
            "anomaly_score"
        ]
    ].head()
)


# ==========================================
# 5. M3 - RULE ENGINE
# ==========================================

print("\nRunning M3 Rule Engine...")

final_output = integrate_m2_m3(df)


# ==========================================
# 6. DISPLAY FINAL RESULTS
# ==========================================

print("\n========== M2 + M3 RESULTS ==========")

print(
    final_output[
        [
            "timestamp",
            "station_id",
            "city",
            "temperature",
            "humidity",
            "pressure",
            "wind_speed",
            "rainfall",
            "ml_status",
            "anomaly_score",
            "rule_anomaly",
            "rule_anomaly_type",
            "rule_feature",
            "rule_reason"
        ]
    ].tail(20)
)


# ==========================================
# 7. SAVE FINAL OUTPUT
# ==========================================

output_path = "../data/m2_m3_integrated_output.csv"

final_output.to_csv(
    output_path,
    index=False
)

print("\n===================================")
print("M2 + M3 Integration Successful!")
print("Saved file:", output_path)
print("===================================")