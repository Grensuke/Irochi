import os
import sys
import uuid
import time
import asyncio
import argparse
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add backend to sys path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.schemas.features import (
    DdosFeatureRecord,
    DdosFeaturePayload,
    ReconFeatureRecord,
    ReconFeaturePayload,
    FeatureMechanism,
    DetectorDomain,
    EntityType,
    WindowType,
)
from app.schemas.detectors import DetectorInput, Decision
from app.services.detectors.ddos import DdosDetector
from app.services.detectors.recon import ReconDetector

DEFAULT_DATASET_ROOT = r"C:\Users\STARK\Documents\Irochi-Data\CIC-IDS2017\GeneratedLabelledFlows\TrafficLabelling"

# =====================================================================
# LEVEL 1: DETECTOR BENCHMARK
# =====================================================================
async def run_level1_benchmark():
    print("\n" + "="*50)
    print("LEVEL 1: DETECTOR BEHAVIOUR BENCHMARK")
    print("="*50)

    # --- DDoS Benchmark ---
    ddos_detector = DdosDetector(packet_rate_threshold=1000.0)
    ddos_matrix = [
        (None, Decision.INSUFFICIENT_DATA),
        (0.0, Decision.NO_THREAT),
        (999.9, Decision.NO_THREAT),
        (1000.0, Decision.NO_THREAT),
        (1000.1, Decision.DETECTION),
        (5000.0, Decision.DETECTION)
    ]

    ddos_passed = True
    print("\n--- DdosDetector Threshold: 1000.0 ---")
    for rate, expected in ddos_matrix:
        payload = DdosFeaturePayload(packet_rate=rate, byte_rate=None, syn_ratio=None, source_ip_entropy=None)
        record = DdosFeatureRecord(
            feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
            detector_domain=DetectorDomain.DDOS, entity_type=EntityType.DESTINATION,
            entity_key="10.0.0.1", window_type=WindowType.TUMBLING,
            window_start=0, window_end=60, computed_at=0, schema_version="1.0",
            revision=1, payload=payload
        )
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id=ddos_detector.detector_id, feature_record=record)
        outputs = await ddos_detector.evaluate([inp])
        actual = outputs[0].decision
        status = "PASS" if actual == expected else "FAIL"
        if status == "FAIL": ddos_passed = False
        print(f"[{status}] packet_rate={rate} -> expected={expected.name}, actual={actual.name}")

    # Test Invalid Schema Type
    recon_record = ReconFeatureRecord(
        feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.RECON, entity_type=EntityType.SOURCE,
        entity_key="10.0.0.1", window_type=WindowType.TUMBLING,
        window_start=0, window_end=3600, computed_at=0, schema_version="1.0",
        revision=1, payload=ReconFeaturePayload(unique_destination_ports=10)
    )
    invalid_inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id=ddos_detector.detector_id, feature_record=recon_record)
    out = await ddos_detector.evaluate([invalid_inp])
    actual_inv = out[0].decision
    status_inv = "PASS" if actual_inv == Decision.INVALID_INPUT else "FAIL"
    if status_inv == "FAIL": ddos_passed = False
    print(f"[{status_inv}] Record Type Mismatch -> expected=INVALID_INPUT, actual={actual_inv.name}")
    print(f"DDoS Level 1 Result: {'PASS ALL' if ddos_passed else 'FAIL'}")

    # --- Recon Benchmark ---
    recon_detector = ReconDetector(portscan_threshold=50)
    recon_matrix = [
        (None, Decision.INSUFFICIENT_DATA),
        (0, Decision.NO_THREAT),
        (49, Decision.NO_THREAT),
        (50, Decision.NO_THREAT),
        (51, Decision.DETECTION),
        (100, Decision.DETECTION)
    ]

    recon_passed = True
    print("\n--- ReconDetector Threshold: 50 ---")
    for ports, expected in recon_matrix:
        payload = ReconFeaturePayload(unique_destination_ports=ports, unique_destination_hosts=None, connection_fan_out=None, scan_rate=None)
        record = ReconFeatureRecord(
            feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
            detector_domain=DetectorDomain.RECON, entity_type=EntityType.SOURCE,
            entity_key="10.0.0.1", window_type=WindowType.TUMBLING,
            window_start=0, window_end=3600, computed_at=0, schema_version="1.0",
            revision=1, payload=payload
        )
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id=recon_detector.detector_id, feature_record=record)
        outputs = await recon_detector.evaluate([inp])
        actual = outputs[0].decision
        status = "PASS" if actual == expected else "FAIL"
        if status == "FAIL": recon_passed = False
        print(f"[{status}] unique_ports={ports} -> expected={expected.name}, actual={actual.name}")

    ddos_record_for_recon = DdosFeatureRecord(
        feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
        detector_domain=DetectorDomain.DDOS, entity_type=EntityType.DESTINATION,
        entity_key="10.0.0.1", window_type=WindowType.TUMBLING,
        window_start=0, window_end=60, computed_at=0, schema_version="1.0",
        revision=1, payload=DdosFeaturePayload(packet_rate=10.0)
    )
    invalid_inp2 = DetectorInput(input_id=str(uuid.uuid4()), detector_id=recon_detector.detector_id, feature_record=ddos_record_for_recon)
    out2 = await recon_detector.evaluate([invalid_inp2])
    actual_inv2 = out2[0].decision
    status_inv2 = "PASS" if actual_inv2 == Decision.INVALID_INPUT else "FAIL"
    if status_inv2 == "FAIL": recon_passed = False
    print(f"[{status_inv2}] Record Type Mismatch -> expected=INVALID_INPUT, actual={actual_inv2.name}")
    print(f"Recon Level 1 Result: {'PASS ALL' if recon_passed else 'FAIL'}")

    return ddos_passed and recon_passed


# =====================================================================
# LEVEL 2: UTILITIES
# =====================================================================

def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    return df

def custom_agg_ddos(group):
    # Total flows
    total_flows = len(group)
    # Attack flows (contains DDoS)
    attack_flows = group['Label'].str.contains('DDoS', na=False).sum()
    # Benign flows
    benign_flows = group['Label'].str.contains('BENIGN', na=False).sum()
    # Other non-benign, non-DDoS flows
    other_flows = total_flows - (attack_flows + benign_flows)

    # Feature
    total_packets = group['Total Fwd Packets'].sum() + group['Total Backward Packets'].sum()

    return pd.Series({
        'Total_Flows': total_flows,
        'Attack_Flows': attack_flows,
        'Benign_Flows': benign_flows,
        'Other_Flows': other_flows,
        'Total_Packets': total_packets
    })

def custom_agg_recon(group):
    total_flows = len(group)
    attack_flows = group['Label'].str.contains('PortScan', na=False).sum()
    benign_flows = group['Label'].str.contains('BENIGN', na=False).sum()
    other_flows = total_flows - (attack_flows + benign_flows)

    unique_ports = group['Destination Port'].nunique()

    return pd.Series({
        'Total_Flows': total_flows,
        'Attack_Flows': attack_flows,
        'Benign_Flows': benign_flows,
        'Other_Flows': other_flows,
        'Unique_Ports': unique_ports
    })

class EvaluatorMetrics:
    def __init__(self):
        self.total_evaluated = 0
        self.attack_windows = 0
        self.pure_benign_windows = 0
        self.mixed_windows = 0

        self.tp = 0
        self.fp = 0
        self.tn = 0
        self.fn = 0

        self.insufficient_data = 0
        self.invalid_input = 0

        self.tp_attack_ratios = []
        self.fn_attack_ratios = []

    def add_result(self, truth: int, pred: int, ratio: float):
        if truth == 1 and pred == 1:
            self.tp += 1
            self.tp_attack_ratios.append(ratio)
        elif truth == 0 and pred == 1:
            self.fp += 1
        elif truth == 0 and pred == 0:
            self.tn += 1
        elif truth == 1 and pred == 0:
            self.fn += 1
            self.fn_attack_ratios.append(ratio)

    def print_report(self, title: str):
        print(f"\n--- {title} Level 2 Results ---")
        print(f"Total Evaluated Windows: {self.total_evaluated}")
        print(f"  Attack Windows (Truth=1): {self.attack_windows}")
        print(f"  Pure Benign Windows (Truth=0): {self.pure_benign_windows}")
        print(f"  Mixed Windows (Attack > 0 & Benign > 0): {self.mixed_windows}")
        print(f"Excluded (INSUFFICIENT_DATA): {self.insufficient_data}")
        print(f"Excluded (INVALID_INPUT): {self.invalid_input}")

        print("\nConfusion Matrix:")
        print(f"  TP: {self.tp}")
        print(f"  FP: {self.fp}")
        print(f"  TN: {self.tn}")
        print(f"  FN: {self.fn}")

        precision = self.tp / (self.tp + self.fp) if (self.tp + self.fp) > 0 else 0
        recall = self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        fpr = self.fp / (self.fp + self.tn) if (self.fp + self.tn) > 0 else 0

        print("\nMetrics:")
        print(f"  Precision: {precision:.4f}")
        print(f"  Recall:    {recall:.4f}")
        print(f"  F1 Score:  {f1:.4f}")
        print(f"  FPR:       {fpr:.4f}")

        avg_tp_ratio = sum(self.tp_attack_ratios)/len(self.tp_attack_ratios) if self.tp_attack_ratios else 0
        avg_fn_ratio = sum(self.fn_attack_ratios)/len(self.fn_attack_ratios) if self.fn_attack_ratios else 0
        print("\nLabel Composition Statistics:")
        print(f"  Avg Attack-Flow Ratio in TP: {avg_tp_ratio:.4f}")
        print(f"  Avg Attack-Flow Ratio in FN: {avg_fn_ratio:.4f}")


# =====================================================================
# LEVEL 2: EVALUATION
# =====================================================================

async def run_level2_ddos(csv_path: str):
    print("\n" + "="*50)
    print(f"LEVEL 2: DDoS EVALUATION -> {csv_path}")
    print("="*50)

    df = pd.read_csv(csv_path, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)

    required = ['Destination IP', 'Timestamp', 'Total Fwd Packets', 'Total Backward Packets', 'Label']
    for col in required:
        if col not in df.columns:
            print(f"Missing column: {col}")
            return

    # Remove rows with null timestamps or critical features
    df = df.dropna(subset=['Timestamp', 'Destination IP', 'Total Fwd Packets', 'Total Backward Packets'])

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True)

    df = df.set_index('Timestamp')
    grouped = df.groupby(['Destination IP', pd.Grouper(freq='60s')])

    aggregated = grouped.apply(custom_agg_ddos).reset_index()
    aggregated = aggregated[aggregated['Total_Flows'] > 0]

    metrics = EvaluatorMetrics()
    detector = DdosDetector(packet_rate_threshold=1000.0)

    inputs = []
    metadata = []

    for idx, row in aggregated.iterrows():
        packet_rate = row['Total_Packets'] / 60.0

        truth = 1 if row['Attack_Flows'] > 0 else 0
        ratio = row['Attack_Flows'] / row['Total_Flows'] if row['Total_Flows'] > 0 else 0

        metrics.total_evaluated += 1
        if truth == 1:
            metrics.attack_windows += 1
            if row['Benign_Flows'] > 0:
                metrics.mixed_windows += 1
        else:
            metrics.pure_benign_windows += 1

        payload = DdosFeaturePayload(packet_rate=packet_rate, byte_rate=None, syn_ratio=None, source_ip_entropy=None)
        record = DdosFeatureRecord(
            feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
            detector_domain=DetectorDomain.DDOS, entity_type=EntityType.DESTINATION,
            entity_key=str(row['Destination IP']), window_type=WindowType.TUMBLING,
            window_start=int(row['Timestamp'].timestamp() * 1000000),
            window_end=int((row['Timestamp'].timestamp() + 60) * 1000000),
            computed_at=int(time.time() * 1000000), schema_version="1.0",
            revision=1, payload=payload
        )
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id=detector.detector_id, feature_record=record)
        inputs.append(inp)
        metadata.append((truth, ratio))

    print(f"Evaluating {len(inputs)} reconstructed windows through DdosDetector...")
    outputs = await detector.evaluate(inputs)

    for out, meta in zip(outputs, metadata):
        truth, ratio = meta
        if out.decision == Decision.INSUFFICIENT_DATA:
            metrics.insufficient_data += 1
        elif out.decision == Decision.INVALID_INPUT:
            metrics.invalid_input += 1
        else:
            pred = 1 if out.decision == Decision.DETECTION else 0
            metrics.add_result(truth, pred, ratio)

    metrics.print_report("DDoS")

async def run_level2_recon(csv_path: str):
    print("\n" + "="*50)
    print(f"LEVEL 2: RECON EVALUATION -> {csv_path}")
    print("="*50)

    df = pd.read_csv(csv_path, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)

    required = ['Source IP', 'Timestamp', 'Destination Port', 'Label']
    for col in required:
        if col not in df.columns:
            print(f"Missing column: {col}")
            return

    df = df.dropna(subset=['Timestamp', 'Source IP', 'Destination Port'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True)

    df = df.set_index('Timestamp')
    grouped = df.groupby(['Source IP', pd.Grouper(freq='3600s')])

    aggregated = grouped.apply(custom_agg_recon).reset_index()
    aggregated = aggregated[aggregated['Total_Flows'] > 0]

    metrics = EvaluatorMetrics()
    detector = ReconDetector(portscan_threshold=50)

    inputs = []
    metadata = []

    for idx, row in aggregated.iterrows():
        truth = 1 if row['Attack_Flows'] > 0 else 0
        ratio = row['Attack_Flows'] / row['Total_Flows'] if row['Total_Flows'] > 0 else 0

        metrics.total_evaluated += 1
        if truth == 1:
            metrics.attack_windows += 1
            if row['Benign_Flows'] > 0:
                metrics.mixed_windows += 1
        else:
            metrics.pure_benign_windows += 1

        payload = ReconFeaturePayload(unique_destination_ports=int(row['Unique_Ports']), unique_destination_hosts=None, connection_fan_out=None, scan_rate=None)
        record = ReconFeatureRecord(
            feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
            detector_domain=DetectorDomain.RECON, entity_type=EntityType.SOURCE,
            entity_key=str(row['Source IP']), window_type=WindowType.TUMBLING,
            window_start=int(row['Timestamp'].timestamp() * 1000000),
            window_end=int((row['Timestamp'].timestamp() + 3600) * 1000000),
            computed_at=int(time.time() * 1000000), schema_version="1.0",
            revision=1, payload=payload
        )
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id=detector.detector_id, feature_record=record)
        inputs.append(inp)
        metadata.append((truth, ratio))

    print(f"Evaluating {len(inputs)} reconstructed windows through ReconDetector...")
    outputs = await detector.evaluate(inputs)

    for out, meta in zip(outputs, metadata):
        truth, ratio = meta
        if out.decision == Decision.INSUFFICIENT_DATA:
            metrics.insufficient_data += 1
        elif out.decision == Decision.INVALID_INPUT:
            metrics.invalid_input += 1
        else:
            pred = 1 if out.decision == Decision.DETECTION else 0
            metrics.add_result(truth, pred, ratio)

    metrics.print_report("Recon")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=str, default=DEFAULT_DATASET_ROOT, help="Path to CIC-IDS2017 TrafficLabelling dir")
    parser.add_argument("--ddos-file", type=str, default="Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
    parser.add_argument("--recon-file", type=str, default="Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv")
    args = parser.parse_args()

    # Level 1
    asyncio.run(run_level1_benchmark())

    # Level 2
    ddos_path = os.path.join(args.dataset_dir, args.ddos_file)
    recon_path = os.path.join(args.dataset_dir, args.recon_file)

    if os.path.exists(ddos_path):
        asyncio.run(run_level2_ddos(ddos_path))
    else:
        print(f"\nDDoS dataset not found: {ddos_path}")

    if os.path.exists(recon_path):
        asyncio.run(run_level2_recon(recon_path))
    else:
        print(f"\nRecon dataset not found: {recon_path}")

if __name__ == "__main__":
    main()
