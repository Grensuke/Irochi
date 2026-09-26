import joblib
import json
import os
import numpy as np
from xgboost import XGBClassifier

MODEL_SAVE_DIR = r"C:\Users\STARK\Documents\Irochi\models"
os.makedirs(MODEL_SAVE_DIR, exist_ok=True)
clf = XGBClassifier(n_estimators=10, max_depth=3, random_state=42)
X = np.array([[1.0, 100.0], [0.1, 10.0]])
y = np.array([1, 0])
clf.fit(X, y)

model_file = os.path.join(MODEL_SAVE_DIR, "exfil_model_v1.joblib")
meta_file = os.path.join(MODEL_SAVE_DIR, "exfil_model_v1.meta.json")

joblib.dump(clf, model_file)

metadata = {
    "model_version": "v1.0.0",
    "model_type": "XGBoost",
    "feature_names": ["outbound_inbound_ratio", "byte_rate"],
    "feature_order": ["outbound_inbound_ratio", "byte_rate"],
    "target_definition": "0=Benign, 1=Infiltration (Exfil proxy)",
    "threshold": 0.50
}
with open(meta_file, 'w') as f:
    json.dump(metadata, f, indent=2)

print("Generated dummy exfil model.")
