"""DNS DGA Model — XGBoost classifier wrapper with rule-based fallback.

Extracts 10 lexical features from domain names and predicts
DGA probability. Falls back to rule-based scoring if model not loaded.
"""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)

MODEL_PATH = Path(__file__).parent / "saved" / "dns_dga.joblib"
BIGRAM_PATH = Path(__file__).parent / "saved" / "dns_dga_bigrams.joblib"

VOWELS = set("aeiou")
CONSONANTS = set("bcdfghjklmnpqrstvwxyz")


class DnsDgaModel:
    """XGBoost DGA classifier with rule-based fallback."""

    def __init__(self) -> None:
        self._model = None
        self._bigram_probs: Optional[dict] = None
        self._loaded = False

    def load(self) -> None:
        """Load both joblib files. Logs if not found."""
        try:
            import joblib
            if MODEL_PATH.exists():
                self._model = joblib.load(MODEL_PATH)
                logger.info("dns_dga_model_loaded", path=str(MODEL_PATH))
            else:
                logger.warning("dns_dga_model_not_found_using_rules", path=str(MODEL_PATH))

            if BIGRAM_PATH.exists():
                self._bigram_probs = joblib.load(BIGRAM_PATH)
                logger.info("dns_dga_bigrams_loaded", path=str(BIGRAM_PATH))
            else:
                logger.warning("dns_dga_bigrams_not_found")

            self._loaded = True
        except Exception as exc:
            logger.error("dns_dga_model_load_failed", error=str(exc))
            self._loaded = True  # Mark as attempted

    def extract_features(self, domain: str) -> list[float]:
        """Extract 10 lexical features from a domain name.

        Features:
            0. domain_entropy     — Shannon entropy of character distribution
            1. domain_length      — Total length of full domain string
            2. label_count        — Number of DNS labels (dots + 1)
            3. max_label_length   — Length of longest label
            4. digit_ratio        — Proportion of digit characters
            5. consonant_ratio    — Proportion of consonant characters
            6. n_gram_score       — Character bigram log-likelihood
            7. vowel_ratio        — Proportion of vowel characters
            8. unique_char_ratio  — Unique characters / total length
            9. is_ip_like         — Does domain look like an IP address
        """
        domain_lower = domain.lower().rstrip(".")
        length = len(domain_lower) or 1

        # 0. Shannon entropy
        freq = {}
        for c in domain_lower:
            freq[c] = freq.get(c, 0) + 1
        entropy = -sum(
            (count / length) * math.log2(count / length)
            for count in freq.values()
            if count > 0
        )

        # 1. Length
        domain_length = float(length)

        # 2. Label count
        labels = domain_lower.split(".")
        label_count = float(len(labels))

        # 3. Max label length
        max_label_length = float(max(len(lbl) for lbl in labels)) if labels else 0.0

        # 4. Digit ratio
        digit_count = sum(1 for c in domain_lower if c.isdigit())
        digit_ratio = digit_count / length

        # 5. Consonant ratio
        alpha_only = re.sub(r"[^a-z]", "", domain_lower)
        alpha_len = len(alpha_only) or 1
        consonant_count = sum(1 for c in alpha_only if c in CONSONANTS)
        consonant_ratio = consonant_count / alpha_len

        # 6. N-gram score
        n_gram_score = self._compute_ngram_score(domain_lower)

        # 7. Vowel ratio
        vowel_count = sum(1 for c in alpha_only if c in VOWELS)
        vowel_ratio = vowel_count / alpha_len

        # 8. Unique char ratio
        unique_chars = len(set(domain_lower))
        unique_char_ratio = unique_chars / length

        # 9. IP-like
        is_ip_like = 1.0 if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", domain_lower) else 0.0

        return [
            entropy, domain_length, label_count, max_label_length,
            digit_ratio, consonant_ratio, n_gram_score,
            vowel_ratio, unique_char_ratio, is_ip_like,
        ]

    def _compute_ngram_score(self, domain: str) -> float:
        """Compute character bigram log-likelihood score."""
        if self._bigram_probs and len(domain) >= 2:
            scores = []
            for i in range(len(domain) - 1):
                bigram = domain[i:i + 2]
                prob = self._bigram_probs.get(bigram, 1e-6)
                scores.append(math.log(prob + 1e-6))
            if scores:
                raw = sum(scores) / len(scores)
                # Normalize to 0-1 range (typical range is -14 to -2)
                return max(0.0, min(1.0, (raw + 14) / 12))
        # Fallback: estimate from character distribution
        alpha_only = re.sub(r"[^a-z]", "", domain)
        if len(alpha_only) < 2:
            return 0.5
        # Count common English bigrams
        common_bigrams = {"th", "he", "in", "er", "an", "re", "on", "at", "en", "nd",
                          "ti", "es", "or", "te", "of", "ed", "is", "it", "al", "ar",
                          "st", "to", "nt", "ng", "se", "ha", "as", "ou", "io", "le"}
        count = sum(1 for i in range(len(alpha_only) - 1)
                    if alpha_only[i:i + 2] in common_bigrams)
        return count / max(len(alpha_only) - 1, 1)

    def predict_proba(self, domain: str) -> float:
        """Predict DGA probability for a domain.

        If model loaded: use XGBoost predict_proba.
        If not loaded: rule-based fallback (max 0.85).
        """
        features = self.extract_features(domain)

        if self._model is not None:
            try:
                import numpy as np
                X = np.array([features])
                proba = self._model.predict_proba(X)[0][1]  # P(DGA)
                return float(proba)
            except Exception as exc:
                logger.warning("dns_dga_prediction_failed_using_rules", error=str(exc))

        # Rule-based fallback
        entropy = features[0]
        length = features[1]
        digit_ratio = features[4]
        ngram_score = features[6]
        vowel_ratio = features[7]

        score = 0.0
        # High entropy → suspicious
        if entropy > 3.5:
            score += 0.25
        if entropy > 4.0:
            score += 0.15
        # Long domain → suspicious
        if length > 30:
            score += 0.15
        if length > 45:
            score += 0.10
        # High digit ratio → suspicious
        if digit_ratio > 0.3:
            score += 0.10
        # Low n-gram score (uncommon bigrams) → suspicious
        if ngram_score < 0.2:
            score += 0.15
        # Low vowel ratio → suspicious
        if vowel_ratio < 0.2:
            score += 0.10

        return min(score, 0.85)  # Cap at 0.85 for rule-based
