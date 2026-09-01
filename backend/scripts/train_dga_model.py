import os
import sys
import json
import time
import datetime
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Add backend to sys path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, precision_score, recall_score, f1_score, roc_auc_score
import joblib

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

# Import exact feature extraction from runtime
from app.services.features.mechanisms import extract_dns_lexical_features

UMUDGA_ROOT = r"C:\Users\STARK\Documents\Irochi-Data\UMUDGA-DATA\UMUDGA - University of Murcia Domain Generation Algorithm Dataset\Fully Qualified Domain Names"
MODEL_SAVE_DIR = r"C:\Users\STARK\Documents\Irochi-Data\models"

def load_umudga_data():
    """Load domains from UMUDGA .list files."""
    data = []
    print(f"Scanning {UMUDGA_ROOT}...")
    for family in os.listdir(UMUDGA_ROOT):
        family_dir = os.path.join(UMUDGA_ROOT, family)
        if not os.path.isdir(family_dir):
            continue

        list_dir = os.path.join(family_dir, "list")
        if not os.path.exists(list_dir):
            continue

        # Prioritize 1k subsets for fast MVP training, we don't need 1M rows for testing pipeline
        # But we will look for 1000.txt to keep the training fast.
        target_file = None
        for size in ["1000.txt", "5000.txt", "10000.txt"]:
            if os.path.exists(os.path.join(list_dir, size)):
                target_file = os.path.join(list_dir, size)
                break

        if not target_file:
            # just take the first file
            files = os.listdir(list_dir)
            if files:
                target_file = os.path.join(list_dir, files[0])

        if target_file:
            is_dga = 0 if family == "legit" else 1
            with open(target_file, 'r', encoding='utf-8') as f:
                for line in f:
                    domain = line.strip()
                    if domain:
                        data.append({"domain": domain, "family": family, "label": is_dga})

    df = pd.DataFrame(data)
    print(f"Loaded {len(df)} total domains across {df['family'].nunique()} families.")
    return df

def clean_data(df):
    """Remove duplicates and handle benign/DGA collisions."""
    initial_len = len(df)

    # 1. Remove exactly identical (domain, label) rows
    df = df.drop_duplicates(subset=["domain", "label"])

    # 2. Check for benign vs DGA collisions (leakage)
    benign_domains = set(df[df["label"] == 0]["domain"])
    dga_domains = set(df[df["label"] == 1]["domain"])

    intersection = benign_domains.intersection(dga_domains)
    print(f"Found {len(intersection)} domains in both legit and DGA sets.")

    # Remove any DGA row that matches a benign domain
    if intersection:
        df = df[~((df["label"] == 1) & (df["domain"].isin(intersection)))]

    print(f"Cleaned dataset: {initial_len} -> {len(df)}")
    return df

def extract_features(df):
    """Extract runtime-compatible features for all domains."""
    print("Extracting features using runtime definitions...")

    features_list = []
    valid_indices = []

    for idx, row in df.iterrows():
        feats = extract_dns_lexical_features(row["domain"])
        if feats is not None:
            features_list.append(feats)
            valid_indices.append(idx)

    feature_df = pd.DataFrame(features_list)
    final_df = df.loc[valid_indices].reset_index(drop=True)

    # Combine
    for col in feature_df.columns:
        final_df[col] = feature_df[col]

    return final_df

def evaluate_model(model, X_train, y_train, X_test, y_test, model_name):
    """Train and evaluate a single model."""
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    t1 = time.time()
    y_pred = model.predict(X_test)
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X_test)[:, 1]
    else:
        y_prob = y_pred
    inf_time = time.time() - t1

    return {
        "model": model_name,
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_prob),
        "train_time_sec": train_time,
        "inf_time_sec": inf_time,
        "model_obj": model
    }

def main():
    os.makedirs(MODEL_SAVE_DIR, exist_ok=True)

    # 1. Load and clean
    df = load_umudga_data()
    df = clean_data(df)
    df = extract_features(df)

    feature_cols = [
        "query_length",
        "label_count",
        "max_label_length",
        "domain_entropy",
        "vowel_consonant_ratio",
        "digit_ratio"
    ]

    # Check for NaN and remove
    initial_len = len(df)
    df = df.dropna(subset=feature_cols)
    print(f"Dropped {initial_len - len(df)} rows due to NaN features.")

    print("\n--- Secondary Validation: Random Stratified Split ---")
    X = df[feature_cols]
    y = df["label"]

    X_train_rnd, X_test_rnd, y_train_rnd, y_test_rnd = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    models = {
        "Logistic Regression": LogisticRegression(max_iter=1000),
        "Random Forest": RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    }
    if HAS_XGB:
        # Hardcode XGBoost out to avoid native crash
        # models["XGBoost"] = XGBClassifier(n_estimators=100, max_depth=6, random_state=42, eval_metric="logloss")
        pass

    for name, clf in models.items():
        try:
            res = evaluate_model(clf, X_train_rnd, y_train_rnd, X_test_rnd, y_test_rnd, name)
            print(f"{name} -> F1: {res['f1']:.4f}, AUC: {res['roc_auc']:.4f}")
        except Exception as e:
            print(f"Error evaluating {name}: {e}")

    print("\n--- Primary Validation: Family-Aware (LOFO) Split ---")
    # Hold out 5 DGA families
    dga_families = df[df["label"] == 1]["family"].unique()
    np.random.seed(42)
    held_out_families = np.random.choice(dga_families, size=min(5, len(dga_families)), replace=False)

    print(f"Held-out DGA families for validation: {held_out_families}")

    train_mask = ~df["family"].isin(held_out_families)
    test_mask = df["family"].isin(held_out_families) | (df["family"] == "legit") # Test against all legit + held out DGA

    X_train_lofo = df[train_mask][feature_cols]
    y_train_lofo = df[train_mask]["label"]

    X_test_lofo = df[test_mask][feature_cols]
    y_test_lofo = df[test_mask]["label"]

    best_f1 = -1
    best_model_name = None
    best_model_obj = None
    best_metrics = {}

    print(f"Train size: {len(X_train_lofo)} | Test size (held-out + legit): {len(X_test_lofo)}")

    for name, clf in models.items():
        res = evaluate_model(clf, X_train_lofo, y_train_lofo, X_test_lofo, y_test_lofo, name)
        print(f"{name} -> F1: {res['f1']:.4f}, AUC: {res['roc_auc']:.4f}, Inf Time: {res['inf_time_sec']:.4f}s")

        if res["f1"] > best_f1:
            best_f1 = res["f1"]
            best_model_name = name
            best_model_obj = res["model_obj"]
            best_metrics = res

    # Decision: Select Random Forest if it's within 0.02 of XGBoost F1 and faster, else best
    # Simple rule: Just pick the highest F1 model in this case for MVP
    selected_model_name = best_model_name
    selected_model_obj = best_model_obj

    print(f"\nSelected Model: {selected_model_name} (F1: {best_metrics['f1']:.4f})")
    print("Rationale: Highest F1 score on held-out DGA families.")

    # Retrain selected model on ALL data for final artifact
    print("Retraining selected model on ALL data...")
    selected_model_obj.fit(X, y)

    # Save Model
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    version = "v1.0.0"

    model_file = os.path.join(MODEL_SAVE_DIR, "dns_dga_model_v1.joblib")
    meta_file = os.path.join(MODEL_SAVE_DIR, "dns_dga_model_v1.meta.json")

    joblib.dump(selected_model_obj, model_file)

    metadata = {
        "model_version": version,
        "model_type": selected_model_name,
        "feature_names": feature_cols,
        "feature_order": feature_cols,
        "target_definition": "0=Benign, 1=DGA",
        "dataset_source": "UMUDGA",
        "training_timestamp": timestamp,
        "preprocessing_definition": "extract_dns_lexical_features from mechanisms.py",
        "evaluation_split_strategy": f"Primary: Family-Aware (Held out {list(held_out_families)}). Secondary: Random Stratified.",
        "evaluation_metrics_heldout": {
            "precision": best_metrics["precision"],
            "recall": best_metrics["recall"],
            "f1": best_metrics["f1"],
            "roc_auc": best_metrics["roc_auc"]
        },
        "threshold": 0.80 # Default, runtime can override
    }

    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nModel saved to: {model_file}")
    print(f"Metadata saved to: {meta_file}")

if __name__ == "__main__":
    main()
