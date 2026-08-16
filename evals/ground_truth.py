import pandas as pd
import os

def _get_df():
    csv_path = os.environ.get("DATASET_PATH", "ai4i2020.csv")
    return pd.read_csv(csv_path)

def overall_failure_rate() -> float:
    df = _get_df()
    return float(df["Machine failure"].sum() / len(df))

def failure_count() -> int:
    df = _get_df()
    return int(df["Machine failure"].sum())

def hdf_count() -> int:
    df = _get_df()
    return int(df["HDF"].sum())

def mean_torque_failed_vs_ok() -> dict:
    df = _get_df()
    return {
        "failed": float(df[df["Machine failure"] == 1]["Torque [Nm]"].mean()),
        "ok": float(df[df["Machine failure"] == 0]["Torque [Nm]"].mean())
    }

def failure_rate_by_type(machine_type: str) -> float:
    df = _get_df()
    sub = df[df["Type"] == machine_type]
    return float(sub["Machine failure"].sum() / len(sub)) if len(sub) > 0 else 0.0