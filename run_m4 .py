import pandas as pd

from m4_processor import process_dataframe


# --------------------------------------------------
# 1. Load M2 + M3 integrated data
# --------------------------------------------------

input_file = "m2_m3_integrated_output.csv.xlsx"

df = pd.read_excel(input_file)

print("Input shape:", df.shape)
print("Input columns:")
print(df.columns.tolist())


# --------------------------------------------------
# 2. Run M4
# --------------------------------------------------

result_df = process_dataframe(df)


# --------------------------------------------------
# 3. Save M4 output
# --------------------------------------------------

output_file = "m2_m3_m4_output.csv"

result_df.to_csv(
    output_file,
    index=False
)


# --------------------------------------------------
# 4. Display basic results
# --------------------------------------------------

print("\nM4 processing completed!")

print("Output shape:", result_df.shape)

print("\nRisk score distribution:")
print(result_df["risk_score"].value_counts().sort_index())

print("\nSeverity distribution:")
print(result_df["severity"].value_counts())

print("\nAnomaly rows:")
print(
    result_df[
        (result_df["ml_prediction"] == 1)
        | (result_df["rule_anomaly"] == True)
    ][
        [
            "timestamp",
            "ml_prediction",
            "anomaly_score",
            "rule_anomaly",
            "rule_anomaly_type",
            "rule_feature",
            "risk_score",
            "confidence",
            "severity",
            "explanation",
            "sensor_health"
        ]
    ]
)

print("\nOutput saved as:", output_file)