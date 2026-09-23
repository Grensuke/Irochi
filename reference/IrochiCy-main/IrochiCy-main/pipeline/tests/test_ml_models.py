"""Tests for ML model wrappers — 4 tests."""

from __future__ import annotations

import pytest

from models.ml.dns_dga_model import DnsDgaModel
from models.ml.exfil_model import ExfilModel


class TestDnsDgaModel:
    def test_dns_dga_feature_extraction_returns_10_floats(self):
        """Feature extraction should return exactly 10 float values."""
        model = DnsDgaModel()
        model.load()
        features = model.extract_features("www.google.com")
        assert len(features) == 10
        assert all(isinstance(f, float) for f in features)

    def test_dns_dga_rule_fallback_when_model_not_loaded(self):
        """Without model file, predict_proba should use rule-based fallback."""
        model = DnsDgaModel()
        model._loaded = True  # Mark as attempted
        model._model = None   # No model loaded

        # Normal domain should score low
        score_normal = model.predict_proba("www.google.com")
        assert score_normal < 0.3

    def test_dns_dga_high_entropy_domain_scores_high(self):
        """High-entropy DGA-like domain should score high even with rules."""
        model = DnsDgaModel()
        model._loaded = True
        model._model = None

        score = model.predict_proba("xnqwkr8j3kd9fh2pzm4bnvc6wt5sa1eo7rlxigy0u.evil")
        assert score > 0.4, f"Expected > 0.4 for DGA domain, got {score}"


class TestExfilModel:
    def test_exfil_rule_fallback_when_model_not_loaded(self):
        """Without model file, predict_proba should use rule-based fallback."""
        model = ExfilModel()
        model._loaded = True
        model._model = None

        # Exfil-like features: high ratio, high bytes, high bps
        features_exfil = [50.0, 1_000_000_000, 100_000_000, 300.0, 1, 1]
        score = model.predict_proba(features_exfil)
        assert score > 0.5, f"Expected > 0.5 for exfil features, got {score}"

        # Normal features
        features_normal = [1.0, 1_000_000, 100_000, 60.0, 0, 0]
        score_normal = model.predict_proba(features_normal)
        assert score_normal < 0.3
