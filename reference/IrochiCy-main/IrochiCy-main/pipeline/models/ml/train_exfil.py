"""Train Exfiltration XGBoost classifier on synthetic data.

Generates synthetic datasets for exfiltration vs normal large transfers,
trains an XGBoost classifier on 6 derived network features.

Usage:
    python -m models.ml.train_exfil
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

SAVE_DIR = Path(__file__).parent / "saved"
MODEL_PATH = SAVE_DIR / "exfil.joblib"


def generate_synthetic_data(n_samples: int = 5000, seed: int = 42):
    """Generate synthetic exfiltration + normal transfer data.

    Returns:
        X: (2*n_samples, 6) feature matrix
        y: (2*n_samples,) labels (1=exfil, 0=normal)
    """
    rng = np.random.default_rng(seed)

    # Positive class (exfiltration)
    exfil_ratio = rng.uniform(10.0, 100.0, n_samples)
    exfil_bytes = rng.integers(524_288_000, 10_737_418_240, n_samples)
    exfil_bps = rng.uniform(10_000_000, 500_000_000, n_samples)
    exfil_duration = rng.uniform(60, 3600, n_samples)
    exfil_port_risk = rng.choice([0, 1], n_samples, p=[0.6, 0.4])
    exfil_encrypted = rng.choice([0, 1], n_samples, p=[0.2, 0.8])

    X_exfil = np.column_stack([
        exfil_ratio, exfil_bytes, exfil_bps,
        exfil_duration, exfil_port_risk, exfil_encrypted,
    ])

    # Negative class (normal large transfer)
    normal_ratio = rng.uniform(0.1, 8.0, n_samples)
    normal_bytes = rng.integers(1_000_000, 500_000_000, n_samples)
    normal_bps = rng.uniform(100_000, 50_000_000, n_samples)
    normal_duration = rng.uniform(10, 7200, n_samples)
    normal_port_risk = np.zeros(n_samples)
    normal_encrypted = rng.choice([0, 1], n_samples, p=[0.4, 0.6])

    X_normal = np.column_stack([
        normal_ratio, normal_bytes, normal_bps,
        normal_duration, normal_port_risk, normal_encrypted,
    ])

    X = np.vstack([X_exfil, X_normal])
    y = np.array([1] * n_samples + [0] * n_samples)

    return X, y


def main() -> None:
    from xgboost import XGBClassifier
    import joblib

    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate data
    print("Generating synthetic exfiltration dataset...")
    X, y = generate_synthetic_data(5000)
    print(f"  Dataset shape: {X.shape}, labels: {np.bincount(y)}")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )

    # Train
    print("Training XGBoost classifier...")
    model = XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        subsample=0.8, colsample_bytree=0.8, random_state=42,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    print("\n=== Classification Report ===")
    print(classification_report(y_test, y_pred, target_names=["Normal", "Exfiltration"]))

    # Save
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved: {MODEL_PATH}")


if __name__ == "__main__":
    main()
