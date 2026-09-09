import os
import sys
import uuid
import time
import asyncio
import pandas as pd
from pathlib import Path

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
from tools.evaluate_detectors import clean_columns, EvaluatorMetrics

DATASET_ROOT = r"C:\Users\STARK\Documents\Irochi-Data\CIC-IDS2017\GeneratedLabelledFlows\TrafficLabelling"

DDOS_FILES = [
    "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Wednesday-workingHours.pcap_ISCX.csv",
    "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv"
]

RECON_FILES = [
    "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
    "Monday-WorkingHours.pcap_ISCX.csv",
    "Tuesday-WorkingHours.pcap_ISCX.csv"
]


def custom_agg_cross_ddos(group):
    total_flows = len(group)
    # We treat both DDoS and DoS as the target threat for the volumetric DdosDetector
    attack_flows = group['Label'].str.contains('DoS|DDoS', na=False, case=False).sum()
    benign_flows = group['Label'].str.contains('BENIGN', na=False).sum()
    other_flows = total_flows - (attack_flows + benign_flows)
    total_packets = group['Total Fwd Packets'].sum() + group['Total Backward Packets'].sum()
    return pd.Series({
        'Total_Flows': total_flows, 'Attack_Flows': attack_flows,
        'Benign_Flows': benign_flows, 'Other_Flows': other_flows,
        'Total_Packets': total_packets
    })

def custom_agg_cross_recon(group):
    total_flows = len(group)
    attack_flows = group['Label'].str.contains('PortScan', na=False).sum()
    benign_flows = group['Label'].str.contains('BENIGN', na=False).sum()
    other_flows = total_flows - (attack_flows + benign_flows)
    unique_ports = group['Destination Port'].nunique()
    return pd.Series({
        'Total_Flows': total_flows, 'Attack_Flows': attack_flows,
        'Benign_Flows': benign_flows, 'Other_Flows': other_flows,
        'Unique_Ports': unique_ports
    })

def calculate_metrics_summary(metrics: EvaluatorMetrics):
    precision = metrics.tp / (metrics.tp + metrics.fp) if (metrics.tp + metrics.fp) > 0 else 0
    recall = metrics.tp / (metrics.tp + metrics.fn) if (metrics.tp + metrics.fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = metrics.fp / (metrics.fp + metrics.tn) if (metrics.fp + metrics.tn) > 0 else 0
    return precision, recall, f1, fpr

async def process_ddos_file(filename, thresholds):
    filepath = os.path.join(DATASET_ROOT, filename)
    df = pd.read_csv(filepath, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)
    if 'Destination IP' not in df.columns:
        return None
    df = df.dropna(subset=['Timestamp', 'Destination IP', 'Total Fwd Packets', 'Total Backward Packets'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True)
    df = df.set_index('Timestamp')
    grouped = df.groupby(['Destination IP', pd.Grouper(freq='60s')])
    aggregated = grouped.apply(custom_agg_cross_ddos).reset_index()
    aggregated = aggregated[aggregated['Total_Flows'] > 0]

    inputs = []
    metadata = []

    for idx, row in aggregated.iterrows():
        packet_rate = row['Total_Packets'] / 60.0
        truth = 1 if row['Attack_Flows'] > 0 else 0
        ratio = row['Attack_Flows'] / row['Total_Flows'] if row['Total_Flows'] > 0 else 0
        payload = DdosFeaturePayload(packet_rate=packet_rate, byte_rate=None, syn_ratio=None, source_ip_entropy=None)
        record = DdosFeatureRecord(
            feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
            detector_domain=DetectorDomain.DDOS, entity_type=EntityType.DESTINATION,
            entity_key=str(row['Destination IP']), window_type=WindowType.TUMBLING,
            window_start=0, window_end=60, computed_at=0, schema_version="1.0",
            revision=1, payload=payload
        )
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id="ddos_detector", feature_record=record)
        inputs.append(inp)
        metadata.append((truth, ratio))

    file_results = {}
    for th in thresholds:
        detector = DdosDetector(packet_rate_threshold=float(th))
        for inp in inputs:
            inp.detector_id = detector.detector_id

        # Batch size limits to avoid memory/event loop blocking if inputs are too huge
        batch_size = 50000
        metrics = EvaluatorMetrics()
        for i in range(0, len(inputs), batch_size):
            batch_inputs = inputs[i:i+batch_size]
            batch_metadata = metadata[i:i+batch_size]
            outputs = await detector.evaluate(batch_inputs)
            for out, meta in zip(outputs, batch_metadata):
                truth, ratio = meta
                if out.decision not in [Decision.INSUFFICIENT_DATA, Decision.INVALID_INPUT]:
                    pred = 1 if out.decision == Decision.DETECTION else 0
                    metrics.add_result(truth, pred, ratio)

        file_results[th] = metrics

    return file_results


async def process_recon_file(filename, thresholds):
    filepath = os.path.join(DATASET_ROOT, filename)
    df = pd.read_csv(filepath, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)
    if 'Source IP' not in df.columns:
        return None
    df = df.dropna(subset=['Timestamp', 'Source IP', 'Destination Port'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True)
    df = df.set_index('Timestamp')
    grouped = df.groupby(['Source IP', pd.Grouper(freq='3600s')])
    aggregated = grouped.apply(custom_agg_cross_recon).reset_index()
    aggregated = aggregated[aggregated['Total_Flows'] > 0]

    inputs = []
    metadata = []

    for idx, row in aggregated.iterrows():
        truth = 1 if row['Attack_Flows'] > 0 else 0
        ratio = row['Attack_Flows'] / row['Total_Flows'] if row['Total_Flows'] > 0 else 0
        payload = ReconFeaturePayload(unique_destination_ports=int(row['Unique_Ports']), unique_destination_hosts=None, connection_fan_out=None, scan_rate=None)
        record = ReconFeatureRecord(
            feature_id=str(uuid.uuid4()), mechanism=FeatureMechanism.WINDOWED,
            detector_domain=DetectorDomain.RECON, entity_type=EntityType.SOURCE,
            entity_key=str(row['Source IP']), window_type=WindowType.TUMBLING,
            window_start=0, window_end=3600, computed_at=0, schema_version="1.0",
            revision=1, payload=payload
        )
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id="recon_detector", feature_record=record)
        inputs.append(inp)
        metadata.append((truth, ratio))

    file_results = {}
    for th in thresholds:
        detector = ReconDetector(portscan_threshold=int(th))
        for inp in inputs:
            inp.detector_id = detector.detector_id

        batch_size = 50000
        metrics = EvaluatorMetrics()
        for i in range(0, len(inputs), batch_size):
            batch_inputs = inputs[i:i+batch_size]
            batch_metadata = metadata[i:i+batch_size]
            outputs = await detector.evaluate(batch_inputs)
            for out, meta in zip(outputs, batch_metadata):
                truth, ratio = meta
                if out.decision not in [Decision.INSUFFICIENT_DATA, Decision.INVALID_INPUT]:
                    pred = 1 if out.decision == Decision.DETECTION else 0
                    metrics.add_result(truth, pred, ratio)
        file_results[th] = metrics

    return file_results

def print_table(results_dict, thresholds):
    print(f"{'Threshold':<10} | {'TP':<5} | {'FP':<5} | {'TN':<5} | {'FN':<5} | {'Precision':<10} | {'Recall':<10} | {'F1':<10} | {'FPR':<10}")
    print("-" * 95)
    for th in thresholds:
        m = results_dict[th]
        p, r, f1, fpr = calculate_metrics_summary(m)
        print(f"{th:<10.1f} | {m.tp:<5} | {m.fp:<5} | {m.tn:<5} | {m.fn:<5} | {p:<10.4f} | {r:<10.4f} | {f1:<10.4f} | {fpr:<10.4f}")

async def run_cross_validation():
    ddos_thresholds = [400, 500, 600, 700]
    recon_thresholds = [200, 300, 400, 500, 700, 900]

    # === DDOS ===
    print("="*80)
    print("DDOS CROSS-DATASET VALIDATION")
    print("="*80)
    ddos_combined = {th: EvaluatorMetrics() for th in ddos_thresholds}
    for file in DDOS_FILES:
        print(f"\nProcessing DDoS File: {file}...")
        res = await process_ddos_file(file, ddos_thresholds)
        if res:
            for th in ddos_thresholds:
                # add to combined
                ddos_combined[th].tp += res[th].tp
                ddos_combined[th].fp += res[th].fp
                ddos_combined[th].tn += res[th].tn
                ddos_combined[th].fn += res[th].fn
            print_table(res, ddos_thresholds)

    print(f"\n>>> COMBINED DDOS RESULTS <<<")
    print_table(ddos_combined, ddos_thresholds)

    # === RECON ===
    print("\n" + "="*80)
    print("RECON CROSS-DATASET VALIDATION")
    print("="*80)
    recon_combined = {th: EvaluatorMetrics() for th in recon_thresholds}
    for file in RECON_FILES:
        print(f"\nProcessing Recon File: {file}...")
        res = await process_recon_file(file, recon_thresholds)
        if res:
            for th in recon_thresholds:
                # add to combined
                recon_combined[th].tp += res[th].tp
                recon_combined[th].fp += res[th].fp
                recon_combined[th].tn += res[th].tn
                recon_combined[th].fn += res[th].fn
            print_table(res, recon_thresholds)

    print(f"\n>>> COMBINED RECON RESULTS <<<")
    print_table(recon_combined, recon_thresholds)

if __name__ == "__main__":
    asyncio.run(run_cross_validation())
