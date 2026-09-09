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
from tools.evaluate_detectors import custom_agg_ddos, custom_agg_recon, clean_columns, EvaluatorMetrics

DATASET_ROOT = r"C:\Users\STARK\Documents\Irochi-Data\CIC-IDS2017\GeneratedLabelledFlows\TrafficLabelling"
DDOS_FILE = os.path.join(DATASET_ROOT, "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
RECON_FILE = os.path.join(DATASET_ROOT, "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv")


def calculate_metrics_summary(metrics: EvaluatorMetrics):
    precision = metrics.tp / (metrics.tp + metrics.fp) if (metrics.tp + metrics.fp) > 0 else 0
    recall = metrics.tp / (metrics.tp + metrics.fn) if (metrics.tp + metrics.fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    fpr = metrics.fp / (metrics.fp + metrics.tn) if (metrics.fp + metrics.tn) > 0 else 0
    return precision, recall, f1, fpr


async def sweep_ddos():
    print("\n" + "="*80)
    print("DDoS THRESHOLD SENSITIVITY SWEEP")
    print("="*80)

    df = pd.read_csv(DDOS_FILE, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)
    df = df.dropna(subset=['Timestamp', 'Destination IP', 'Total Fwd Packets', 'Total Backward Packets'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True)
    df = df.set_index('Timestamp')
    grouped = df.groupby(['Destination IP', pd.Grouper(freq='60s')])
    aggregated = grouped.apply(custom_agg_ddos).reset_index()
    aggregated = aggregated[aggregated['Total_Flows'] > 0]

    inputs = []
    metadata = []

    attack_w = 0
    benign_w = 0
    mixed_w = 0

    for idx, row in aggregated.iterrows():
        packet_rate = row['Total_Packets'] / 60.0
        truth = 1 if row['Attack_Flows'] > 0 else 0
        ratio = row['Attack_Flows'] / row['Total_Flows'] if row['Total_Flows'] > 0 else 0

        if truth == 1:
            attack_w += 1
            if row['Benign_Flows'] > 0:
                mixed_w += 1
        else:
            benign_w += 1

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
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id="ddos_detector", feature_record=record)
        inputs.append(inp)
        metadata.append((truth, ratio))

    print(f"Total Evaluated Windows: {len(inputs)}")
    print(f"Attack Windows: {attack_w} | Pure Benign: {benign_w} | Mixed: {mixed_w}\n")

    thresholds = [400, 500, 600, 700, 750, 800, 850, 900, 950, 1000]
    results = []

    print(f"{'Threshold':<10} | {'TP':<5} | {'FP':<5} | {'TN':<5} | {'FN':<5} | {'Precision':<10} | {'Recall':<10} | {'F1':<10} | {'FPR':<10}")
    print("-" * 95)

    for th in thresholds:
        detector = DdosDetector(packet_rate_threshold=float(th))
        for inp in inputs:
            inp.detector_id = detector.detector_id

        outputs = await detector.evaluate(inputs)
        metrics = EvaluatorMetrics()

        for out, meta in zip(outputs, metadata):
            truth, ratio = meta
            if out.decision not in [Decision.INSUFFICIENT_DATA, Decision.INVALID_INPUT]:
                pred = 1 if out.decision == Decision.DETECTION else 0
                metrics.add_result(truth, pred, ratio)

        p, r, f1, fpr = calculate_metrics_summary(metrics)
        results.append({
            'th': th, 'tp': metrics.tp, 'fp': metrics.fp, 'tn': metrics.tn, 'fn': metrics.fn,
            'p': p, 'r': r, 'f1': f1, 'fpr': fpr
        })

        print(f"{th:<10.1f} | {metrics.tp:<5} | {metrics.fp:<5} | {metrics.tn:<5} | {metrics.fn:<5} | {p:<10.4f} | {r:<10.4f} | {f1:<10.4f} | {fpr:<10.4f}")

    print("\nBest DDoS Thresholds:")
    print(f"Highest F1:        {max(results, key=lambda x: x['f1'])['th']:.1f}")
    print(f"Highest Recall:    {max(results, key=lambda x: x['r'])['th']:.1f}")
    print(f"Highest Precision: {max(results, key=lambda x: x['p'])['th']:.1f} (tie-breaks not handled natively)")
    print(f"Lowest FPR:        {min(results, key=lambda x: x['fpr'])['th']:.1f}")


async def sweep_recon():
    print("\n" + "="*80)
    print("RECON THRESHOLD SENSITIVITY SWEEP")
    print("="*80)

    df = pd.read_csv(RECON_FILE, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)
    df = df.dropna(subset=['Timestamp', 'Source IP', 'Destination Port'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True)
    df = df.set_index('Timestamp')
    grouped = df.groupby(['Source IP', pd.Grouper(freq='3600s')])
    aggregated = grouped.apply(custom_agg_recon).reset_index()
    aggregated = aggregated[aggregated['Total_Flows'] > 0]

    inputs = []
    metadata = []

    attack_w = 0
    benign_w = 0
    mixed_w = 0

    for idx, row in aggregated.iterrows():
        truth = 1 if row['Attack_Flows'] > 0 else 0
        ratio = row['Attack_Flows'] / row['Total_Flows'] if row['Total_Flows'] > 0 else 0

        if truth == 1:
            attack_w += 1
            if row['Benign_Flows'] > 0:
                mixed_w += 1
        else:
            benign_w += 1

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
        inp = DetectorInput(input_id=str(uuid.uuid4()), detector_id="recon_detector", feature_record=record)
        inputs.append(inp)
        metadata.append((truth, ratio))

    print(f"Total Evaluated Windows: {len(inputs)}")
    print(f"Attack Windows: {attack_w} | Pure Benign: {benign_w} | Mixed: {mixed_w}\n")

    thresholds = [50, 75, 100, 150, 200, 300, 400, 500, 600, 700, 800, 900]
    results = []

    print(f"{'Threshold':<10} | {'TP':<5} | {'FP':<5} | {'TN':<5} | {'FN':<5} | {'Precision':<10} | {'Recall':<10} | {'F1':<10} | {'FPR':<10}")
    print("-" * 95)

    for th in thresholds:
        detector = ReconDetector(portscan_threshold=int(th))
        for inp in inputs:
            inp.detector_id = detector.detector_id

        outputs = await detector.evaluate(inputs)
        metrics = EvaluatorMetrics()

        for out, meta in zip(outputs, metadata):
            truth, ratio = meta
            if out.decision not in [Decision.INSUFFICIENT_DATA, Decision.INVALID_INPUT]:
                pred = 1 if out.decision == Decision.DETECTION else 0
                metrics.add_result(truth, pred, ratio)

        p, r, f1, fpr = calculate_metrics_summary(metrics)
        results.append({
            'th': th, 'tp': metrics.tp, 'fp': metrics.fp, 'tn': metrics.tn, 'fn': metrics.fn,
            'p': p, 'r': r, 'f1': f1, 'fpr': fpr
        })

        print(f"{th:<10.1f} | {metrics.tp:<5} | {metrics.fp:<5} | {metrics.tn:<5} | {metrics.fn:<5} | {p:<10.4f} | {r:<10.4f} | {f1:<10.4f} | {fpr:<10.4f}")

    print("\nBest Recon Thresholds:")
    print(f"Highest F1:        {max(results, key=lambda x: x['f1'])['th']:.1f}")
    print(f"Highest Recall:    {max(results, key=lambda x: x['r'])['th']:.1f}")
    print(f"Highest Precision: {max(results, key=lambda x: x['p'])['th']:.1f} (tie-breaks not handled natively)")
    print(f"Lowest FPR:        {min(results, key=lambda x: x['fpr'])['th']:.1f}")


if __name__ == "__main__":
    asyncio.run(sweep_ddos())
    asyncio.run(sweep_recon())
