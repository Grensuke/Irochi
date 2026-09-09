import os
import sys
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from tools.evaluate_detectors import custom_agg_ddos, custom_agg_recon, clean_columns

DATASET_ROOT = r"C:\Users\STARK\Documents\Irochi-Data\CIC-IDS2017\GeneratedLabelledFlows\TrafficLabelling"
DDOS_FILE = os.path.join(DATASET_ROOT, "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv")
RECON_FILE = os.path.join(DATASET_ROOT, "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv")

def analyze_ddos():
    print("\n" + "="*50)
    print("DDoS DIAGNOSTIC ANALYSIS")
    print("="*50)

    df = pd.read_csv(DDOS_FILE, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)

    total_raw_rows = len(df)
    print(f"Exact raw rows: {total_raw_rows}")
    print("Label distribution:")
    print(df['Label'].value_counts())

    initial_len = len(df)
    df = df.dropna(subset=['Timestamp', 'Destination IP', 'Total Fwd Packets', 'Total Backward Packets'])
    dropped = initial_len - len(df)
    print(f"Malformed/skipped rows: {dropped}")

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True)
    df = df.set_index('Timestamp')
    grouped = df.groupby(['Destination IP', pd.Grouper(freq='60s')])

    aggregated = grouped.apply(custom_agg_ddos).reset_index()
    aggregated = aggregated[aggregated['Total_Flows'] > 0].copy()

    print(f"Exact reconstructed windows: {len(aggregated)}")

    aggregated['Packet_Rate'] = aggregated['Total_Packets'] / 60.0
    aggregated['Truth'] = aggregated['Attack_Flows'].apply(lambda x: 1 if x > 0 else 0)
    aggregated['Prediction'] = aggregated['Packet_Rate'].apply(lambda x: 1 if x > 1000.0 else 0)

    # 1. & 2. Analyze the 22 Attack Windows
    attack_windows = aggregated[aggregated['Truth'] == 1].copy()
    print(f"\n--- 1 & 2. Attack Windows Analysis (Total: {len(attack_windows)}) ---")

    for idx, row in attack_windows.iterrows():
        status = "TP" if row['Prediction'] == 1 else "FN (Missed)"
        ratio = row['Attack_Flows'] / row['Total_Flows']
        print(f"[{status}] DestIP: {row['Destination IP']:<15} | Window Start: {row['Timestamp']} | "
              f"Rate: {row['Packet_Rate']:<8.2f} pps | Flows (Tot/Att/Ben/Oth): {row['Total_Flows']}/{row['Attack_Flows']}/{row['Benign_Flows']}/{row['Other_Flows']} | Ratio: {ratio:.2f}")

    # 3. Packet_Rate Stats
    tp_windows = aggregated[(aggregated['Truth'] == 1) & (aggregated['Prediction'] == 1)]
    fn_windows = aggregated[(aggregated['Truth'] == 1) & (aggregated['Prediction'] == 0)]
    pure_benign = aggregated[aggregated['Truth'] == 0]

    print("\n--- 3. Packet_Rate Statistics (pps) ---")
    def print_stats(name, subset):
        if len(subset) == 0:
            print(f"{name:<12} | N=0")
        else:
            print(f"{name:<12} | N={len(subset):<5} | Min: {subset['Packet_Rate'].min():<8.2f} | Max: {subset['Packet_Rate'].max():<8.2f} | Mean: {subset['Packet_Rate'].mean():<8.2f} | Median: {subset['Packet_Rate'].median():<8.2f}")

    print_stats("TP Windows", tp_windows)
    print_stats("FN Windows", fn_windows)
    print_stats("Pure Benign", pure_benign)

def analyze_recon():
    print("\n" + "="*50)
    print("RECON DIAGNOSTIC ANALYSIS")
    print("="*50)

    df = pd.read_csv(RECON_FILE, encoding='cp1252', engine='python', on_bad_lines='skip')
    df = clean_columns(df)

    total_raw_rows = len(df)
    print(f"Exact raw rows: {total_raw_rows}")
    print("Label distribution:")
    print(df['Label'].value_counts())

    initial_len = len(df)
    df = df.dropna(subset=['Timestamp', 'Source IP', 'Destination Port'])
    dropped = initial_len - len(df)
    print(f"Malformed/skipped rows: {dropped}")

    df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed', dayfirst=True)
    df = df.set_index('Timestamp')
    grouped = df.groupby(['Source IP', pd.Grouper(freq='3600s')])

    aggregated = grouped.apply(custom_agg_recon).reset_index()
    aggregated = aggregated[aggregated['Total_Flows'] > 0].copy()

    print(f"Exact reconstructed windows: {len(aggregated)}")

    aggregated['Truth'] = aggregated['Attack_Flows'].apply(lambda x: 1 if x > 0 else 0)
    aggregated['Prediction'] = aggregated['Unique_Ports'].apply(lambda x: 1 if x > 50 else 0)

    fp_windows = aggregated[(aggregated['Truth'] == 0) & (aggregated['Prediction'] == 1)]
    print(f"\n--- 1. False Positive Windows (Total: {len(fp_windows)}) ---")

    for idx, row in fp_windows.iterrows():
        ratio = row['Attack_Flows'] / row['Total_Flows']
        print(f"[FP] SrcIP: {row['Source IP']:<15} | Window Start: {row['Timestamp']} | "
              f"Unique Ports: {row['Unique_Ports']:<4} | Flows (Tot/Att/Ben/Oth): {row['Total_Flows']}/{row['Attack_Flows']}/{row['Benign_Flows']}/{row['Other_Flows']} | Ratio: {ratio:.2f}")

    # 2. Stats
    tp_windows = aggregated[(aggregated['Truth'] == 1) & (aggregated['Prediction'] == 1)]
    fn_windows = aggregated[(aggregated['Truth'] == 1) & (aggregated['Prediction'] == 0)]
    tn_windows = aggregated[(aggregated['Truth'] == 0) & (aggregated['Prediction'] == 0)]

    print("\n--- 2. Unique Destination Ports Statistics ---")
    def print_stats(name, subset):
        if len(subset) == 0:
            print(f"{name:<12} | N=0")
        else:
            print(f"{name:<12} | N={len(subset):<5} | Min: {subset['Unique_Ports'].min():<6} | Max: {subset['Unique_Ports'].max():<6} | Mean: {subset['Unique_Ports'].mean():<6.2f} | Median: {subset['Unique_Ports'].median():<6.2f}")

    print_stats("TP Windows", tp_windows)
    print_stats("FN Windows", fn_windows)
    print_stats("FP Windows", fp_windows)
    print_stats("TN Windows", tn_windows)


if __name__ == "__main__":
    analyze_ddos()
    analyze_recon()
