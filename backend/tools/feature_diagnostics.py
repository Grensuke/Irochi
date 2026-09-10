import pandas as pd
import numpy as np
import argparse
import sys
import os

def compute_ddos_features(group, window_size=60):
    packet_rate = (group['Total Fwd Packets'].sum() + group['Total Backward Packets'].sum()) / window_size
    byte_rate = (group['Total Length of Fwd Packets'].sum() + group['Total Length of Bwd Packets'].sum()) / window_size

    total_conns = len(group)
    syn_conns = group['Fwd PSH Flags'].sum() # Approximation
    syn_ratio = syn_conns / total_conns if total_conns > 0 else 0.0

    unique_sources = group['Source IP'].nunique()
    source_ip_entropy = np.log2(max(unique_sources, 1))

    return pd.Series({
        'packet_rate': packet_rate,
        'byte_rate': byte_rate,
        'syn_ratio': syn_ratio,
        'source_ip_entropy': source_ip_entropy
    })

def compute_recon_features(group, window_size=3600):
    unique_ports = group['Destination Port'].nunique()
    unique_hosts = group['Destination IP'].nunique()
    total_conns = len(group)
    scan_rate = total_conns / window_size
    connection_fan_out = unique_hosts / max(total_conns, 1)

    return pd.Series({
        'unique_destination_ports': unique_ports,
        'unique_destination_hosts': unique_hosts,
        'scan_rate': scan_rate,
        'connection_fan_out': connection_fan_out
    })

def load_and_aggregate(filepath, domain):
    df = pd.read_csv(filepath, skipinitialspace=True, encoding='latin1')
    df.columns = df.columns.str.strip()

    # Map label presence
    if domain == 'ddos':
        df['Label_Match'] = df['Label'].str.contains('DDoS|DoS', na=False, regex=True)
        # Group by Destination IP and 60s windows
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed')
        df['Window'] = df['Timestamp'].dt.floor('60s')
        grouped = df.groupby(['Destination IP', 'Window'])
        features = grouped.apply(compute_ddos_features, include_groups=False).reset_index()
        # Agg labels
        labels = grouped.apply(lambda x: x['Label_Match'].sum() > 0, include_groups=False).reset_index(name='Is_Malicious')
        features = pd.merge(features, labels, on=['Destination IP', 'Window'])
    elif domain == 'recon':
        df['Label_Match'] = df['Label'].str.contains('PortScan', na=False, regex=True)
        # Group by Source IP and 3600s windows
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed')
        df['Window'] = df['Timestamp'].dt.floor('3600s')
        grouped = df.groupby(['Source IP', 'Window'])
        features = grouped.apply(compute_recon_features, include_groups=False).reset_index()
        # Agg labels
        labels = grouped.apply(lambda x: x['Label_Match'].sum() > 0, include_groups=False).reset_index(name='Is_Malicious')
        features = pd.merge(features, labels, on=['Source IP', 'Window'])

    return features

def report_distributions(df, columns):
    for col in columns:
        print(f"--- {col} ---")
        for is_malicious in [True, False]:
            subset = df[df['Is_Malicious'] == is_malicious][col]
            if len(subset) == 0:
                continue

            label_str = "TP/FN (Malicious)" if is_malicious else "TN/FP (Benign)"
            print(f"  {label_str} [N={len(subset)}]:")
            print(f"    Min: {subset.min():.4f}")
            print(f"    Max: {subset.max():.4f}")
            print(f"    Mean: {subset.mean():.4f}")
            print(f"    Median: {subset.median():.4f}")
            print(f"    p25: {subset.quantile(0.25):.4f}")
            print(f"    p75: {subset.quantile(0.75):.4f}")
            print(f"    p90: {subset.quantile(0.90):.4f}")
            print(f"    p95: {subset.quantile(0.95):.4f}")
            print(f"    p99: {subset.quantile(0.99):.4f}")
        print()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-dir', required=True)
    args = parser.parse_args()

    ddos_files = [
        "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
        "Monday-WorkingHours.pcap_ISCX.csv",
        "Wednesday-workingHours.pcap_ISCX.csv",
        "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv"
    ]

    print("=== DDOS FEATURE DISTRIBUTIONS ===")
    ddos_df_list = []
    for f in ddos_files:
        filepath = os.path.join(args.dataset_dir, f)
        if os.path.exists(filepath):
            print(f"Processing {f}...")
            ddos_df_list.append(load_and_aggregate(filepath, 'ddos'))
        else:
            print(f"Skipping {f} - not found.")

    if ddos_df_list:
        combined_ddos = pd.concat(ddos_df_list)
        report_distributions(combined_ddos, ['packet_rate', 'byte_rate', 'syn_ratio', 'source_ip_entropy'])

    recon_files = [
        "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
        "Monday-WorkingHours.pcap_ISCX.csv",
        "Tuesday-WorkingHours.pcap_ISCX.csv"
    ]

    print("=== RECON FEATURE DISTRIBUTIONS ===")
    recon_df_list = []
    for f in recon_files:
        filepath = os.path.join(args.dataset_dir, f)
        if os.path.exists(filepath):
            print(f"Processing {f}...")
            recon_df_list.append(load_and_aggregate(filepath, 'recon'))
        else:
            print(f"Skipping {f} - not found.")

    if recon_df_list:
        combined_recon = pd.concat(recon_df_list)
        report_distributions(combined_recon, ['unique_destination_ports', 'unique_destination_hosts', 'scan_rate', 'connection_fan_out'])

if __name__ == '__main__':
    main()
