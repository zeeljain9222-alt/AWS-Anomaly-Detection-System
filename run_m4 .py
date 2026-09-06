import pandas as pd

from m4_processor import (
    process_dataframe
)


# -----------------------------
# FILE NAMES
# -----------------------------

INPUT_FILE = (
    "m2_m3_integrated_output.csv"
)

OUTPUT_FILE = (
    "m2_m3_m4_output.csv"
)


# -----------------------------
# READ DATA
# -----------------------------

df = pd.read_csv(
    INPUT_FILE
)


print(
    "Input shape:",
    df.shape
)


print(
    "\nInput columns:"
)

print(
    list(df.columns)
)


# -----------------------------
# RUN M4
# -----------------------------

result_df = process_dataframe(
    df
)


# -----------------------------
# DISPLAY RESULTS
# -----------------------------

print(
    "\nOutput shape:",
    result_df.shape
)


print(
    "\nML status:"
)

print(
    result_df[
        "ml_status"
    ].value_counts()
)


print(
    "\nRule anomalies:"
)

print(
    result_df[
        "rule_anomaly"
    ].value_counts()
)


print(
    "\nSeverity:"
)

print(
    result_df[
        "severity"
    ].value_counts()
)


print(
    "\nRisk distribution:"
)

print(
    result_df[
        "risk_score"
    ].value_counts().sort_index()
)


# -----------------------------
# SAVE OUTPUT
# -----------------------------

result_df.to_csv(
    OUTPUT_FILE,
    index=False
)


print(
    f"\nM4 output saved to: "
    f"{OUTPUT_FILE}"
)