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
from sklearn.metrics import classification_report, precision_score, recall_score, f1_score, roc_auc_score
import joblib

try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    print("XGBoost is not installed. Exiting.")
    sys.exit(1)

DATASET_PATH = r"C:\Users\STARK\Documents\Irochi-Data\CIC-IDS2017\GeneratedLabelledFlows\TrafficLabelling\Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv"
MODEL_SAVE_DIR = r"C:\Users\STARK\Documents\Irochi-Data\models"

def load_and_preprocess_data():
    print(f"Loading {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH, encoding='cp1252') # common with CIC-IDS
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    print(f"Loaded {len(df)} rows. Extracting labels and features...")
    
    # Extract Label
    df['label'] = df['Label'].apply(lambda x: 1 if x != 'BENIGN' else 0)
    
    # Calculate Features (matching ExfiltrationDetector schema logic)
    # byte_rate = (Total Length of Fwd Packets + Total Length of Bwd Packets) / (Flow Duration / 1e6)
    duration_s = df['Flow Duration'].replace(0, 1) / 1e6
    df['byte_rate'] = (df['Total Length of Fwd Packets'] + df['Total Length of Bwd Packets']) / duration_s
    
    # outbound_inbound_ratio = Fwd Length / (Bwd Length + 1)
    df['outbound_inbound_ratio'] = df['Total Length of Fwd Packets'] / (df['Total Length of Bwd Packets'] + 1)
    
    # Clean up infinities and NaNs
    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)
    
    print(f"Dataset summary: {len(df)} rows, {df['label'].sum()} malicious.")
    return df

def evaluate_model(model, X_train, y_train, X_test, y_test, model_name):
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    t1 = time.time()
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    inf_time = time.time() - t1

    return {
        "model": model_name,
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_test, y_prob) if len(np.unique(y_test)) > 1 else 0.0,
        "train_time_sec": train_time,
        "inf_time_sec": inf_time,
        "model_obj": model
    }

def main():
    os.makedirs(MODEL_SAVE_DIR, exist_ok=True)

    df = load_and_preprocess_data()
    
    feature_cols = ['outbound_inbound_ratio', 'byte_rate']
    
    print("\n--- Leakage-Aware Split (Hold-out by Source IP) ---")
    unique_ips = df['Source IP'].unique()
    np.random.seed(42)
    test_ips = np.random.choice(unique_ips, size=int(len(unique_ips) * 0.2), replace=False)
    
    train_mask = ~df['Source IP'].isin(test_ips)
    test_mask = df['Source IP'].isin(test_ips)
    
    X_train = df[train_mask][feature_cols]
    y_train = df[train_mask]['label']
    
    X_test = df[test_mask][feature_cols]
    y_test = df[test_mask]['label']
    
    print(f"Train size: {len(X_train)} | Test size: {len(X_test)}")
    
    clf = XGBClassifier(n_estimators=100, max_depth=6, random_state=42, eval_metric="logloss")
    
    res = evaluate_model(clf, X_train, y_train, X_test, y_test, "XGBoost Exfiltration")
    print(f"Evaluation -> F1: {res['f1']:.4f}, AUC: {res['roc_auc']:.4f}, Inf Time: {res['inf_time_sec']:.4f}s")
    
    # Retrain on ALL data for final model artifact
    print("\nRetraining model on ALL data...")
    X_all = df[feature_cols]
    y_all = df['label']
    clf.fit(X_all, y_all)
    
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    version = "v1.0.0"
    
    model_file = os.path.join(MODEL_SAVE_DIR, "exfil_model_v1.joblib")
    meta_file = os.path.join(MODEL_SAVE_DIR, "exfil_model_v1.meta.json")
    
    joblib.dump(clf, model_file)
    
    metadata = {
        "model_version": version,
        "model_type": "XGBoost",
        "feature_names": feature_cols,
        "feature_order": feature_cols,
        "target_definition": "0=Benign, 1=Infiltration (Exfil proxy)",
        "dataset_source": "CIC-IDS2017 (Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv)",
        "training_timestamp": timestamp,
        "evaluation_split_strategy": "Source IP Holdout (20%)",
        "evaluation_metrics_heldout": {
            "precision": res["precision"],
            "recall": res["recall"],
            "f1": res["f1"],
            "roc_auc": res["roc_auc"]
        },
        "threshold": 0.50 # Default, runtime can override
    }
    
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
        
    print(f"\nModel saved to: {model_file}")
    print(f"Metadata saved to: {meta_file}")

if __name__ == "__main__":
    main()
