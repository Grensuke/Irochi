import os
import sys
import uuid
import time
import asyncio
import argparse
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

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
from app.schemas.detectors import DetectorInput, Decision, DetectorOutput, ThreatType, SourceFeatureReference, DetectorId
from app.services.detectors.ddos import DdosDetector
from app.services.detectors.recon import ReconDetector

DEFAULT_DATASET_ROOT = r"C:\Users\STARK\Documents\Irochi-Data\CIC-IDS2017\GeneratedLabelledFlows\TrafficLabelling"

# =====================================================================
# LEGACY BASELINES
# =====================================================================

class LegacyDdosDetector:
    def __init__(self, packet_rate_threshold: float = 1000.0):
        self.packet_rate_threshold = packet_rate_threshold

    @property
    def detector_id(self) -> DetectorId: return DetectorId.DDOS

    async def evaluate(self, inputs: List[DetectorInput]) -> List[DetectorOutput]:
        outputs = []
        for inp in inputs:
            record = inp.feature_record
            if not isinstance(record, DdosFeatureRecord):
                outputs.append(self._create_output(inp, Decision.INVALID_INPUT, evidence={"reason": "Expected DdosFeatureRecord"}))
                continue
            packet_rate = record.payload.packet_rate
            if packet_rate is None:
                outputs.append(self._create_output(inp, Decision.INSUFFICIENT_DATA, evidence={"reason": "packet_rate is missing"}))
                continue
            if packet_rate > self.packet_rate_threshold:
                decision = Decision.DETECTION
            else:
                decision = Decision.NO_THREAT
            outputs.append(self._create_output(inp, decision, score=float(packet_rate)))
        return outputs

    def _create_output(self, inp, decision, score=None, evidence=None):
        return DetectorOutput(
            output_id=str(uuid.uuid4()), detector_id=DetectorId.DDOS, input_id=inp.input_id,
            entity_type=inp.feature_record.entity_type, entity_key=inp.feature_record.entity_key,
            evaluated_at=0, detector_version="1.0.0", decision=decision, threat_type=ThreatType.VOLUMETRIC_DDOS,
            score=score, evidence=evidence, source_feature_references=[]
        )

class LegacyReconDetector:
    def __init__(self, portscan_threshold: int = 50):
        self.portscan_threshold = portscan_threshold

    @property
    def detector_id(self) -> DetectorId: return DetectorId.RECON

    async def evaluate(self, inputs: List[DetectorInput]) -> List[DetectorOutput]:
        outputs = []
        for inp in inputs:
            record = inp.feature_record
            if not isinstance(record, ReconFeatureRecord):
                outputs.append(self._create_output(inp, Decision.INVALID_INPUT, evidence={"reason": "Expected ReconFeatureRecord"}))
                continue
            unique_ports = record.payload.unique_destination_ports
            if unique_ports is None:
                outputs.append(self._create_output(inp, Decision.INSUFFICIENT_DATA, evidence={"reason": "unique_destination_ports is missing"}))
                continue
            if unique_ports > self.portscan_threshold:
                decision = Decision.DETECTION
            else:
                decision = Decision.NO_THREAT
            outputs.append(self._create_output(inp, decision, score=float(unique_ports)))
        return outputs

    def _create_output(self, inp, decision, score=None, evidence=None):
        return DetectorOutput(
            output_id=str(uuid.uuid4()), detector_id=DetectorId.RECON, input_id=inp.input_id,
            entity_type=inp.feature_record.entity_type, entity_key=inp.feature_record.entity_key,
            evaluated_at=0, detector_version="1.0.0", decision=decision, threat_type=ThreatType.RECON_PORTSCAN,
            score=score, evidence=evidence, source_feature_references=[]
        )

# =====================================================================
# UTILITIES
# =====================================================================

def clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    return df

def custom_agg_ddos(group):
    total_flows = len(group)
    attack_flows = group['Label'].str.contains('DDoS|DoS', na=False, regex=True).sum()
    benign_flows = group['Label'].str.contains('BENIGN', na=False).sum()
    other_flows = total_flows - (attack_flows + benign_flows)

    total_packets = group['Total Fwd Packets'].sum() + group['Total Backward Packets'].sum()

    # Safe fallback if bytes column name differs slightly across CIC files
    byte_col_fwd = 'Total Length of Fwd Packets' if 'Total Length of Fwd Packets' in group.columns else 'Total Length of Fwd Packet'
    byte_col_bwd = 'Total Length of Bwd Packets' if 'Total Length of Bwd Packets' in group.columns else 'Total Length of Bwd Packet'
    total_bytes = group[byte_col_fwd].sum() + group[byte_col_bwd].sum() if byte_col_fwd in group.columns and byte_col_bwd in group.columns else 0

    # SYN flag fallback
    syn_col = 'SYN Flag Count'
    syn_conns = group[syn_col].sum() if syn_col in group.columns else 0

    return pd.Series({
        'Total_Flows': total_flows,
        'Attack_Flows': attack_flows,
        'Benign_Flows': benign_flows,
        'Other_Flows': other_flows,
        'Total_Packets': total_packets,
        'Total_Bytes': total_bytes,
        'Syn_Conns': syn_conns,
        'Unique_Src': group['Source IP'].nunique()
    })

def custom_agg_recon(group):
    total_flows = len(group)
    attack_flows = group['Label'].str.contains('PortScan', na=False).sum()
    benign_flows = group['Label'].str.contains('BENIGN', na=False).sum()
    other_flows = total_flows - (attack_flows + benign_flows)

    unique_ports = group['Destination Port'].nunique()
    unique_hosts = group['Destination IP'].nunique()

    return pd.Series({
        'Total_Flows': total_flows,
        'Attack_Flows': attack_flows,
        'Benign_Flows': benign_flows,
        'Other_Flows': other_flows,
        'Unique_Ports': unique_ports,
        'Unique_Hosts': unique_hosts
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

    def add_result(self, truth: int, pred: int):
        if truth == 1 and pred == 1: self.tp += 1
        elif truth == 0 and pred == 1: self.fp += 1
        elif truth == 0 and pred == 0: self.tn += 1
        elif truth == 1 and pred == 0: self.fn += 1

    def print_report(self, title: str):
        print(f"\n--- {title} Results ---")
        precision = self.tp / (self.tp + self.fp) if (self.tp + self.fp) > 0 else 0
        recall = self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        fpr = self.fp / (self.fp + self.tn) if (self.fp + self.tn) > 0 else 0

        print(f"  TP: {self.tp} | FP: {self.fp} | TN: {self.tn} | FN: {self.fn}")
        print(f"  Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f} | FPR: {fpr:.4f}")

# =====================================================================
# EVALUATION
# =====================================================================

async def evaluate_ddos_dataset(csv_path: str, compare: bool, threshold_config: dict = None):
    print("\n" + "="*50)
    print(f"EVALUATING DDoS -> {csv_path}")
    print("="*50)

    df = pd.read_csv(csv_path, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)

    for col in ['Destination IP', 'Timestamp', 'Total Fwd Packets', 'Total Backward Packets', 'Label', 'Source IP']:
        if col not in df.columns:
            print(f"Missing column: {col}")
            return

    df = df.dropna(subset=['Timestamp', 'Destination IP', 'Total Fwd Packets', 'Total Backward Packets'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True)

    df = df.set_index('Timestamp')
    grouped = df.groupby(['Destination IP', pd.Grouper(freq='60s')])
    aggregated = grouped.apply(custom_agg_ddos).reset_index()
    aggregated = aggregated[aggregated['Total_Flows'] > 0]

    baseline_metrics = EvaluatorMetrics()
    improved_metrics = EvaluatorMetrics()

    baseline_detector = LegacyDdosDetector()
    kwargs = {}
    if threshold_config:
        kwargs['thresholds'] = threshold_config
    improved_detector = DdosDetector(**kwargs)

    inputs = []
    metadata = []

    import math

    for idx, row in aggregated.iterrows():
        packet_rate = row['Total_Packets'] / 60.0
        byte_rate = row['Total_Bytes'] / 60.0 if 'Total_Bytes' in row else 0.0
        syn_ratio = row['Syn_Conns'] / row['Total_Flows'] if 'Syn_Conns' in row and row['Total_Flows'] > 0 else 0.0
        source_ip_entropy = math.log2(max(row['Unique_Src'], 1))

        truth = 1 if row['Attack_Flows'] > 0 else 0

        payload = DdosFeaturePayload(
            packet_rate=packet_rate, byte_rate=byte_rate, syn_ratio=syn_ratio, source_ip_entropy=source_ip_entropy
        )
        record = DdosFeatureRecord(
            feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
            detector_domain=DetectorDomain.DDOS, entity_type=EntityType.DESTINATION,
            entity_key=str(row['Destination IP']), window_type=WindowType.TUMBLING,
            window_start=int(row['Timestamp'].timestamp() * 1000000),
            window_end=int((row['Timestamp'].timestamp() + 60) * 1000000),
            computed_at=int(time.time() * 1000000), schema_version="1.0",
            revision=1, payload=payload
        )
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id=baseline_detector.detector_id, feature_record=record)
        inputs.append(inp)
        metadata.append(truth)

    print(f"Evaluating {len(inputs)} reconstructed windows...")

    if compare:
        out_b = await baseline_detector.evaluate(inputs)
        out_i = await improved_detector.evaluate(inputs)

        for b, i, truth in zip(out_b, out_i, metadata):
            pred_b = 1 if b.decision == Decision.DETECTION else 0
            pred_i = 1 if i.decision == Decision.DETECTION else 0
            baseline_metrics.add_result(truth, pred_b)
            improved_metrics.add_result(truth, pred_i)

        baseline_metrics.print_report("DDoS BASELINE")
        improved_metrics.print_report("DDoS IMPROVED")
    else:
        out_i = await improved_detector.evaluate(inputs)
        for i, truth in zip(out_i, metadata):
            pred_i = 1 if i.decision == Decision.DETECTION else 0
            improved_metrics.add_result(truth, pred_i)
        improved_metrics.print_report("DDoS IMPROVED")

async def evaluate_recon_dataset(csv_path: str, compare: bool, threshold_config: dict = None):
    print("\n" + "="*50)
    print(f"EVALUATING RECON -> {csv_path}")
    print("="*50)

    df = pd.read_csv(csv_path, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)

    required = ['Source IP', 'Timestamp', 'Destination Port', 'Label', 'Destination IP']
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

    baseline_metrics = EvaluatorMetrics()
    improved_metrics = EvaluatorMetrics()

    baseline_detector = LegacyReconDetector()
    kwargs = {}
    if threshold_config:
        kwargs['thresholds'] = threshold_config
    improved_detector = ReconDetector(**kwargs)

    inputs = []
    metadata = []

    for idx, row in aggregated.iterrows():
        truth = 1 if row['Attack_Flows'] > 0 else 0

        unique_ports = int(row['Unique_Ports'])
        unique_hosts = int(row['Unique_Hosts'])
        scan_rate = row['Total_Flows'] / 3600.0
        connection_fan_out = unique_hosts / max(row['Total_Flows'], 1)

        payload = ReconFeaturePayload(
            unique_destination_ports=unique_ports,
            unique_destination_hosts=unique_hosts,
            connection_fan_out=connection_fan_out,
            scan_rate=scan_rate
        )
        record = ReconFeatureRecord(
            feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
            detector_domain=DetectorDomain.RECON, entity_type=EntityType.SOURCE,
            entity_key=str(row['Source IP']), window_type=WindowType.TUMBLING,
            window_start=int(row['Timestamp'].timestamp() * 1000000),
            window_end=int((row['Timestamp'].timestamp() + 3600) * 1000000),
            computed_at=int(time.time() * 1000000), schema_version="1.0",
            revision=1, payload=payload
        )
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id=baseline_detector.detector_id, feature_record=record)
        inputs.append(inp)
        metadata.append(truth)

    print(f"Evaluating {len(inputs)} reconstructed windows...")

    if compare:
        out_b = await baseline_detector.evaluate(inputs)
        out_i = await improved_detector.evaluate(inputs)

        for b, i, truth in zip(out_b, out_i, metadata):
            pred_b = 1 if b.decision == Decision.DETECTION else 0
            pred_i = 1 if i.decision == Decision.DETECTION else 0
            baseline_metrics.add_result(truth, pred_b)
            improved_metrics.add_result(truth, pred_i)

        baseline_metrics.print_report("Recon BASELINE")
        improved_metrics.print_report("Recon IMPROVED")
    else:
        out_i = await improved_detector.evaluate(inputs)
        for i, truth in zip(out_i, metadata):
            pred_i = 1 if i.decision == Decision.DETECTION else 0
            improved_metrics.add_result(truth, pred_i)
        improved_metrics.print_report("Recon IMPROVED")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=str, default=DEFAULT_DATASET_ROOT, help="Path to CIC-IDS2017 TrafficLabelling dir")
    parser.add_argument("--ddos-file", type=str, default="Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
    parser.add_argument("--recon-file", type=str, default="Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv")
    parser.add_argument("--compare", action="store_true", help="Compare Baseline vs Improved models")
    args = parser.parse_args()

    ddos_path = os.path.join(args.dataset_dir, args.ddos_file)
    recon_path = os.path.join(args.dataset_dir, args.recon_file)

    if os.path.exists(ddos_path):
        asyncio.run(evaluate_ddos_dataset(ddos_path, args.compare))
    else:
        print(f"\nDDoS dataset not found: {ddos_path}")

    if os.path.exists(recon_path):
        asyncio.run(evaluate_recon_dataset(recon_path, args.compare))
    else:
        print(f"\nRecon dataset not found: {recon_path}")

if __name__ == "__main__":
    main()
