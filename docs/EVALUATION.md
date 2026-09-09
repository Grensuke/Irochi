# Irochi Detector Evaluation

This document outlines the evaluation methodology and findings for the Irochi detection pipeline. It separates the formal testing (Level 1) from the dataset-driven evaluation (Level 2).

## Evaluation Levels

### Level 1: Detector Behaviour Benchmark (Implemented & Tested)
Level 1 is a synthetic, deterministic test suite that invokes the real detector classes directly with carefully constructed `FeatureRecords`.
- **Goal**: Verify that the implemented logic exactly matches the intended thresholds and handles edge cases (e.g., missing values).
- **Scope**: Includes exact boundary tests around the current thresholds.

### Level 2: CIC-IDS2017 Methodology (Evaluated)
Level 2 evaluates the detectors against the external CIC-IDS2017 dataset.
- **Dataset Source**: `C:\Users\STARK\Documents\Irochi-Data\CIC-IDS2017\GeneratedLabelledFlows\TrafficLabelling\`
- **Ground Truth Definition**: "A window is malicious if it contains at least one flow explicitly labeled with the target attack." (Incident-presence evaluation).
- **Tooling**: `evaluate_detectors.py`, `diagnostic_analysis.py`, `sensitivity_analysis.py`, and `cross_validation.py`. This tooling runs the real detector logic against the dataset offline without modifying the production detector code.

## Findings & Baseline Results

### DDoS Baseline & Diagnostic Findings
- **Baseline Results**: Evaluated against the Friday working hours dataset containing volumetric/protocol DDoS attacks.
- **Diagnostic Findings**: The default `1000 pps` threshold produced multiple false negatives (21 FN windows). Further analysis revealed that these missed attacks were often slow-rate application-layer DoS (like Hulk) operating significantly below 1000 pps.

### Recon Baseline & Diagnostic Findings
- **Baseline Results**: Evaluated against the Friday working hours dataset containing PortScan attacks.
- **Diagnostic Findings**: The default `50` unique ports threshold successfully detects recon, but generates false positives in noisy benign traffic (e.g., heavily multiplexed web traffic).

### Flow-to-Window Reconstruction Limitation (Known Limitation)
The current evaluation methodology reconstructs tumbling feature windows from offline flow records (PCAP-extracted flows). This causes artificial "burstiness" because the real-time inter-arrival spacing of packets is lost when aggregated. This heavily penalizes simple rate-based detection and limits the accuracy of the offline evaluation compared to live packet processing.

## Threshold Sensitivity & Cross-Dataset Validation

### Sensitivity Analysis (Evaluated)
- Swept DDoS thresholds from 400 to 1000 pps.
- Swept Recon thresholds from 50 to 900 unique ports.

### Cross-Dataset Validation (Evaluated)
- Evaluated the candidate thresholds against other days (Monday - Thursday).
- **DDoS Candidates (500-600 pps)**: Improved recall on Friday, but introduced false positives on other days due to natural spikes in background traffic.
- **Recon Candidate (900 ports)**: Substantially reduced false positives on Friday, but the baseline benign port utilization varied significantly across different days, meaning the 900 threshold did not fully generalize to zero FPs.
- **Conclusion**: Candidate thresholds **did not fully generalize** across the datasets.

### Improved Multi-Signal Detectors (Evaluated)
- The improved Recon multi-signal model successfully halved false positives on the Friday baseline (FP reduced from 26 to 10) while maintaining true positive recall. This was achieved by heavily weighting connection-fan-out (horizontal scanning characteristics) rather than relying solely on raw unique port counts.
- The improved DDoS multi-signal model demonstrated that the strict multi-dimensional thresholds (`packet_rate`, `byte_rate`, `syn_ratio`, `source_entropy`) effectively eliminate benign anomalies, but are overly restrictive for application-layer DoS attacks (e.g. Wednesday DoS Hulk dataset), producing 0 True Positives under current stringent defaults.

## Current Production Defaults

The production defaults for the new multi-signal models are kept restrictive by design to ensure zero false positives, pending cross-dataset validation to find optimal production weights. Candidate thresholds from the evaluation are treated as evaluation insights.

- **DDoS Detector**: Multi-signal model (requires combination of `packet_rate`, `byte_rate`, `syn_ratio`, and `source_entropy` meeting `confidence_cutoff > 0.6`).
- **Recon Detector**: Multi-signal model (requires combination of `unique_ports`, `unique_hosts`, `scan_rate`, and `connection_fan_out` meeting `confidence_cutoff > 0.6`).
- **DNS/DGA Detector**: Uses a loaded `.joblib` model. *(Note: DGA is implemented in code but requires the external model artifact to function. Without it, it yields a `DETECTOR_ERROR` and is not fully runtime-ready.)*

## Status Definitions
- **Implemented**: The code exists in the repository.
- **Tested**: Verified via automated `pytest` suites (e.g., `test_streaming.py`).
- **Evaluated**: Run through the Level 2 dataset evaluation harness.
- **Candidate Improvement**: A proposed change based on evaluation (e.g., 600 pps) that is not yet active in production.
- **Known Limitation**: A verified architectural or evaluation constraint (e.g., flow-distortion, model dependency).
