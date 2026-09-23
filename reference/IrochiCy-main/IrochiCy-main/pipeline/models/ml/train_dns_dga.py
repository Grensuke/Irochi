"""Train DNS DGA XGBoost classifier.

Downloads DGA domains from Bambenek feed and legitimate domains from
Umbrella top-1M list, trains an XGBoost classifier on 10 lexical features.

Usage:
    python -m models.ml.train_dns_dga
"""

from __future__ import annotations

import io
import math
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split

SAVE_DIR = Path(__file__).parent / "saved"
MODEL_PATH = SAVE_DIR / "dns_dga.joblib"
BIGRAM_PATH = SAVE_DIR / "dns_dga_bigrams.joblib"

BAMBENEK_URL = "https://osint.bambenekconsulting.com/feeds/dga-feed-high.csv"
UMBRELLA_URL = "https://s3-us-west-1.amazonaws.com/umbrella-static/top-1m.csv.zip"

VOWELS = set("aeiou")
CONSONANTS = set("bcdfghjklmnpqrstvwxyz")


def download_dga_domains(max_domains: int = 50000) -> list[str]:
    """Download DGA domains from Bambenek feed."""
    import httpx

    print(f"Downloading DGA domains from Bambenek...")
    resp = httpx.get(BAMBENEK_URL, timeout=60, follow_redirects=True)
    domains = []
    for line in resp.text.strip().split("\n"):
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split(",")
        if parts:
            domain = parts[0].strip().lower().rstrip(".")
            if domain and "." in domain:
                domains.append(domain)
        if len(domains) >= max_domains:
            break
    print(f"  Downloaded {len(domains)} DGA domains")
    return domains


def download_legitimate_domains(max_domains: int = 50000) -> list[str]:
    """Download legitimate domains from Umbrella top-1M."""
    import httpx

    print(f"Downloading legitimate domains from Umbrella top-1M...")
    resp = httpx.get(UMBRELLA_URL, timeout=60, follow_redirects=True)
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_name = zf.namelist()[0]
        with zf.open(csv_name) as f:
            content = f.read().decode("utf-8")
    domains = []
    for line in content.strip().split("\n"):
        parts = line.split(",")
        if len(parts) >= 2:
            domain = parts[1].strip().lower().rstrip(".")
            if domain and "." in domain:
                domains.append(domain)
        if len(domains) >= max_domains:
            break
    print(f"  Downloaded {len(domains)} legitimate domains")
    return domains


def build_bigram_model(domains: list[str]) -> dict[str, float]:
    """Build character bigram probability model from legitimate domains."""
    counter = Counter()
    total = 0
    for domain in domains:
        clean = re.sub(r"[^a-z]", "", domain.lower())
        for i in range(len(clean) - 1):
            counter[clean[i:i + 2]] += 1
            total += 1
    probs = {bigram: count / total for bigram, count in counter.items()}
    return probs


def extract_features(domain: str, bigram_probs: dict) -> list[float]:
    """Extract 10 lexical features from a domain."""
    domain_lower = domain.lower().rstrip(".")
    length = len(domain_lower) or 1

    # Entropy
    freq = {}
    for c in domain_lower:
        freq[c] = freq.get(c, 0) + 1
    entropy = -sum(
        (cnt / length) * math.log2(cnt / length)
        for cnt in freq.values() if cnt > 0
    )

    labels = domain_lower.split(".")
    label_count = float(len(labels))
    max_label_length = float(max(len(lbl) for lbl in labels)) if labels else 0.0

    digit_count = sum(1 for c in domain_lower if c.isdigit())
    digit_ratio = digit_count / length

    alpha_only = re.sub(r"[^a-z]", "", domain_lower)
    alpha_len = len(alpha_only) or 1
    consonant_ratio = sum(1 for c in alpha_only if c in CONSONANTS) / alpha_len
    vowel_ratio = sum(1 for c in alpha_only if c in VOWELS) / alpha_len

    # N-gram score
    if len(domain_lower) >= 2:
        scores = []
        for i in range(len(domain_lower) - 1):
            prob = bigram_probs.get(domain_lower[i:i + 2], 1e-6)
            scores.append(math.log(prob + 1e-6))
        ngram_score = sum(scores) / len(scores) if scores else -14.0
        ngram_score = max(0.0, min(1.0, (ngram_score + 14) / 12))
    else:
        ngram_score = 0.5

    unique_char_ratio = len(set(domain_lower)) / length
    is_ip_like = 1.0 if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain_lower) else 0.0

    return [entropy, float(length), label_count, max_label_length,
            digit_ratio, consonant_ratio, ngram_score, vowel_ratio,
            unique_char_ratio, is_ip_like]


def main() -> None:
    from xgboost import XGBClassifier
    import joblib

    SAVE_DIR.mkdir(parents=True, exist_ok=True)

    # Download datasets
    try:
        dga_domains = download_dga_domains(50000)
        legit_domains = download_legitimate_domains(50000)
    except Exception as exc:
        print(f"Download failed: {exc}")
        print("Using synthetic fallback dataset...")
        # Synthetic fallback
        import random
        random.seed(42)
        chars = "abcdefghijklmnopqrstuvwxyz0123456789"
        dga_domains = [
            "".join(random.choices(chars, k=random.randint(15, 40))) + ".com"
            for _ in range(5000)
        ]
        legit_domains = [
            f"www.{word}.com" for word in
            ["google", "facebook", "amazon", "microsoft", "apple", "github",
             "stackoverflow", "reddit", "wikipedia", "youtube"] * 500
        ]

    # Build bigram model from legitimate domains
    print("Building bigram model...")
    bigram_probs = build_bigram_model(legit_domains)
    joblib.dump(bigram_probs, BIGRAM_PATH)
    print(f"  Saved bigram model: {BIGRAM_PATH}")

    # Balance dataset
    min_size = min(len(dga_domains), len(legit_domains))
    dga_domains = dga_domains[:min_size]
    legit_domains = legit_domains[:min_size]

    # Extract features
    print("Extracting features...")
    X_dga = [extract_features(d, bigram_probs) for d in dga_domains]
    X_legit = [extract_features(d, bigram_probs) for d in legit_domains]

    X = np.array(X_dga + X_legit)
    y = np.array([1] * len(X_dga) + [0] * len(X_legit))

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
    print(classification_report(y_test, y_pred, target_names=["Legitimate", "DGA"]))

    # Save
    joblib.dump(model, MODEL_PATH)
    print(f"\nModel saved: {MODEL_PATH}")
    print(f"Bigrams saved: {BIGRAM_PATH}")


if __name__ == "__main__":
    main()
