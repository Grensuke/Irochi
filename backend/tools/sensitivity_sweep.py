import pandas as pd
import numpy as np
import itertools
import argparse
import sys
import os

# --- FEATURE RECONSTRUCTION (Same as feature_diagnostics.py) ---
def compute_ddos_features(group, window_size=60):
    packet_rate = (group['Total Fwd Packets'].sum() + group['Total Backward Packets'].sum()) / window_size
    byte_rate = (group['Total Length of Fwd Packets'].sum() + group['Total Length of Bwd Packets'].sum()) / window_size

    total_conns = len(group)
    syn_conns = group['Fwd PSH Flags'].sum()
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
    df = pd.read_csv(filepath, skipinitialspace=True, encoding='latin1', low_memory=False)
    df.columns = df.columns.str.strip()

    if domain == 'ddos':
        df['Label_Match'] = df['Label'].str.contains('DDoS|DoS', na=False, regex=True)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed')
        df['Window'] = df['Timestamp'].dt.floor('60s')
        grouped = df.groupby(['Destination IP', 'Window'])
        features = grouped.apply(compute_ddos_features, include_groups=False).reset_index()
        labels = grouped.apply(lambda x: x['Label_Match'].sum() > 0, include_groups=False).reset_index(name='Is_Malicious')
        features = pd.merge(features, labels, on=['Destination IP', 'Window'])
    elif domain == 'recon':
        df['Label_Match'] = df['Label'].str.contains('PortScan', na=False, regex=True)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='mixed')
        df['Window'] = df['Timestamp'].dt.floor('3600s')
        grouped = df.groupby(['Source IP', 'Window'])
        features = grouped.apply(compute_recon_features, include_groups=False).reset_index()
        labels = grouped.apply(lambda x: x['Label_Match'].sum() > 0, include_groups=False).reset_index(name='Is_Malicious')
        features = pd.merge(features, labels, on=['Source IP', 'Window'])

    return features

# --- EVALUATOR ---
def evaluate_grid(df, grid, domain):
    results = []

    if domain == 'ddos':
        feature_cols = ['packet_rate', 'byte_rate', 'syn_ratio', 'source_ip_entropy']
    else:
        feature_cols = ['unique_destination_ports', 'unique_destination_hosts', 'scan_rate', 'connection_fan_out']

    # Vectorize logic across the whole DataFrame to avoid slow iteration
    vals = df[feature_cols].values
    is_malicious = df['Is_Malicious'].values
    N = len(df)

    for conf in grid:
        # conf format: (thresh_1, thresh_2, thresh_3, thresh_4, w1, w2, w3, w4, min_triggers, cutoff)
        t = np.array(conf[0:4], dtype=float)
        w = np.array(conf[4:8], dtype=float)
        min_triggers = conf[8]
        cutoff = conf[9]

        # Avoid division by zero
        t_safe = np.where(t == 0, 1e-9, t)

        # score = min(val / thresh, 1.0)
        scores = np.clip(vals / t_safe, 0.0, 1.0)

        # Handle missing (simulated missing is NaN, but we don't have NaN in computed windows)
        # However, packet_rate/ports are strictly required, if missing -> INSUFFICIENT_DATA

        triggered = scores >= 0.5
        triggered_counts = triggered.sum(axis=1)

        confidence = np.clip(np.sum(scores * w, axis=1), 0.0, 1.0)

        detections = (triggered_counts >= min_triggers) & (confidence > cutoff)

        tp = np.sum(detections & is_malicious)
        fp = np.sum(detections & ~is_malicious)
        fn = np.sum(~detections & is_malicious)
        tn = np.sum(~detections & ~is_malicious)

        # Calculate per-signal trigger rates for TP and FP to report signal utility
        tp_mask = detections & is_malicious
        fp_mask = detections & ~is_malicious

        signal_trigger_rates_tp = triggered[tp_mask].mean(axis=0) if tp > 0 else np.zeros(4)
        signal_trigger_rates_fp = triggered[fp_mask].mean(axis=0) if fp > 0 else np.zeros(4)

        results.append({
            'config': conf,
            'TP': tp, 'FP': fp, 'TN': tn, 'FN': fn,
            'signal_trigger_tp': signal_trigger_rates_tp,
            'signal_trigger_fp': signal_trigger_rates_fp
        })

    return results

def compute_metrics(tp, fp, tn, fn):
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    return precision, recall, f1, fpr

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset-dir', required=True)
    args = parser.parse_args()

    # ---------------------------------------------------------
    # DDoS SWEEP
    # ---------------------------------------------------------
    print("Loading DDoS Tuning datasets...")
    df_ddos_fri = load_and_aggregate(os.path.join(args.dataset_dir, "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"), 'ddos')
    df_ddos_mon = load_and_aggregate(os.path.join(args.dataset_dir, "Monday-WorkingHours.pcap_ISCX.csv"), 'ddos')
    df_ddos_tuning = pd.concat([df_ddos_fri, df_ddos_mon])

    print("Loading DDoS Validation datasets...")
    df_ddos_wed = load_and_aggregate(os.path.join(args.dataset_dir, "Wednesday-workingHours.pcap_ISCX.csv"), 'ddos')
    # Use WebAttacks or Infiltration for Thursday
    df_ddos_thu = load_and_aggregate(os.path.join(args.dataset_dir, "Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv"), 'ddos')
    df_ddos_val = pd.concat([df_ddos_wed, df_ddos_thu])

    # Grid definition
    t_packet_rate = [50.0, 200.0, 500.0, 1000.0]
    t_byte_rate = [10000.0, 50000.0, 200000.0]
    t_syn_ratio = [0.30, 0.70]
    t_source_ip_entropy = [2.0, 5.0]
    w_profiles_ddos = [
        (0.25, 0.25, 0.25, 0.25),          # Balanced
        (0.40, 0.10, 0.10, 0.40),          # Rate-heavy (packet/byte)
        (0.10, 0.40, 0.40, 0.10)           # Context-heavy (syn/diversity)
    ]
    min_triggers_ddos = [1, 2]
    cutoffs_ddos = [0.25, 0.35, 0.45, 0.50, 0.60]

    ddos_grid = list(itertools.product(
        t_packet_rate, t_byte_rate, t_syn_ratio, t_source_ip_entropy,
        [w[0] for w in w_profiles_ddos],  # Extract weights to match lengths, wait simpler to combine directly
    ))

    ddos_grid_full = []
    for t_pr, t_br, t_sr, t_sie in itertools.product(t_packet_rate, t_byte_rate, t_syn_ratio, t_source_ip_entropy):
        for w in w_profiles_ddos:
            for mt in min_triggers_ddos:
                for c in cutoffs_ddos:
                    ddos_grid_full.append((t_pr, t_br, t_sr, t_sie, w[0], w[1], w[2], w[3], mt, c))

    print(f"DDoS Grid combinations: {len(ddos_grid_full)}")

    print("Evaluating DDoS Tuning...")
    ddos_tune_res = evaluate_grid(df_ddos_tuning, ddos_grid_full, 'ddos')
    print("Evaluating DDoS Validation...")
    ddos_val_res = evaluate_grid(df_ddos_val, ddos_grid_full, 'ddos')

    # Analyze DDoS
    ddos_candidates = []
    for i, t_res in enumerate(ddos_tune_res):
        v_res = ddos_val_res[i]

        t_prec, t_rec, t_f1, t_fpr = compute_metrics(t_res['TP'], t_res['FP'], t_res['TN'], t_res['FN'])
        v_prec, v_rec, v_f1, v_fpr = compute_metrics(v_res['TP'], v_res['FP'], v_res['TN'], v_res['FN'])
        if t_fpr <= 0.01 and v_fpr <= 0.01 and t_rec > 0 and v_rec > 0:
            ddos_candidates.append({
                'config': t_res['config'],
                't_f1': t_f1, 'v_f1': v_f1,
                't_rec': t_rec, 'v_rec': v_rec,
                't_fpr': t_fpr, 'v_fpr': v_fpr,
                't_res': t_res, 'v_res': v_res
            })

    ddos_candidates.sort(key=lambda x: (x['t_f1'], x['v_f1']), reverse=True)

    # ---------------------------------------------------------
    # RECON SWEEP
    # ---------------------------------------------------------
    print("\nLoading Recon Datasets...")
    df_recon_fri = load_and_aggregate(os.path.join(args.dataset_dir, "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv"), 'recon')

    # SPLIT FRIDAY at window boundary
    windows = sorted(df_recon_fri['Window'].unique())
    split_point = windows[len(windows) // 2]

    df_recon_fri_tune = df_recon_fri[df_recon_fri['Window'] < split_point]
    df_recon_fri_val = df_recon_fri[df_recon_fri['Window'] >= split_point]

    df_recon_mon = load_and_aggregate(os.path.join(args.dataset_dir, "Monday-WorkingHours.pcap_ISCX.csv"), 'recon')
    df_recon_tue = load_and_aggregate(os.path.join(args.dataset_dir, "Tuesday-WorkingHours.pcap_ISCX.csv"), 'recon')

    df_recon_tuning = pd.concat([df_recon_fri_tune, df_recon_mon])
    df_recon_val = pd.concat([df_recon_fri_val, df_recon_tue])

    t_ports = [50.0, 150.0, 500.0]
    t_hosts = [5.0, 50.0]
    t_scan_rate = [1.0, 10.0, 50.0]
    t_fan_out = [0.5, 0.8]
    w_profiles_recon = [
        (0.25, 0.25, 0.25, 0.25),
        (0.40, 0.10, 0.40, 0.10), # Vertical heavy
        (0.10, 0.40, 0.10, 0.40)  # Horizontal heavy
    ]
    min_triggers_recon = [1, 2]
    cutoffs_recon = [0.25, 0.35, 0.45, 0.50, 0.60]

    recon_grid_full = []
    for t_p, t_h, t_sr, t_fo in itertools.product(t_ports, t_hosts, t_scan_rate, t_fan_out):
        for w in w_profiles_recon:
            for mt in min_triggers_recon:
                for c in cutoffs_recon:
                    recon_grid_full.append((t_p, t_h, t_sr, t_fo, w[0], w[1], w[2], w[3], mt, c))

    print(f"Recon Grid combinations: {len(recon_grid_full)}")

    print("Evaluating Recon Tuning...")
    recon_tune_res = evaluate_grid(df_recon_tuning, recon_grid_full, 'recon')
    print("Evaluating Recon Validation...")
    recon_val_res = evaluate_grid(df_recon_val, recon_grid_full, 'recon')

    recon_candidates = []
    for i, t_res in enumerate(recon_tune_res):
        v_res = recon_val_res[i]

        t_prec, t_rec, t_f1, t_fpr = compute_metrics(t_res['TP'], t_res['FP'], t_res['TN'], t_res['FN'])
        v_prec, v_rec, v_f1, v_fpr = compute_metrics(v_res['TP'], v_res['FP'], v_res['TN'], v_res['FN'])
        if True:
            recon_candidates.append({
                'config': t_res['config'],
                't_f1': t_f1, 'v_f1': v_f1,
                't_rec': t_rec, 'v_rec': v_rec,
                't_fpr': t_fpr, 'v_fpr': v_fpr,
                't_res': t_res, 'v_res': v_res
            })

    recon_candidates.sort(key=lambda x: (x['t_f1'], x['v_f1']), reverse=True)

    # ---------------------------------------------------------
    # PRINT REPORT
    # ---------------------------------------------------------
    print("\n==================================================")
    print("DDOS TOP 3 CANDIDATES")
    print("==================================================")
    for c in ddos_candidates[:3]:
        conf = c['config']
        print(f"Config: packet_rate={conf[0]}, byte_rate={conf[1]}, syn_ratio={conf[2]}, src_div={conf[3]}")
        print(f"        weights=({conf[4]}, {conf[5]}, {conf[6]}, {conf[7]}), min_triggers={conf[8]}, cutoff={conf[9]}")
        print(f"Tuning (Fri+Mon): F1={c['t_f1']:.4f}, Recall={c['t_rec']:.4f}, FPR={c['t_fpr']:.4f}")
        print(f"Valid  (Wed+Thu): F1={c['v_f1']:.4f}, Recall={c['v_rec']:.4f}, FPR={c['v_fpr']:.4f}")
        print(f"Signal Triggers (TP): PR={c['t_res']['signal_trigger_tp'][0]:.2f}, BR={c['t_res']['signal_trigger_tp'][1]:.2f}, SR={c['t_res']['signal_trigger_tp'][2]:.2f}, SD={c['t_res']['signal_trigger_tp'][3]:.2f}")
        print(f"Signal Triggers (FP): PR={c['t_res']['signal_trigger_fp'][0]:.2f}, BR={c['t_res']['signal_trigger_fp'][1]:.2f}, SR={c['t_res']['signal_trigger_fp'][2]:.2f}, SD={c['t_res']['signal_trigger_fp'][3]:.2f}")
        print()

    if not ddos_candidates:
        print("No DDoS configurations met the FPR and Recall constraints.")

    print("==================================================")
    print("RECON TOP 3 CANDIDATES")
    print("==================================================")
    for c in recon_candidates[:3]:
        conf = c['config']
        print(f"Config: ports={conf[0]}, hosts={conf[1]}, scan_rate={conf[2]}, fan_out={conf[3]}")
        print(f"        weights=({conf[4]}, {conf[5]}, {conf[6]}, {conf[7]}), min_triggers={conf[8]}, cutoff={conf[9]}")
        print(f"Tuning (Fri_H1+Mon): F1={c['t_f1']:.4f}, Recall={c['t_rec']:.4f}, FPR={c['t_fpr']:.4f}")
        print(f"Valid  (Fri_H2+Tue): F1={c['v_f1']:.4f}, Recall={c['v_rec']:.4f}, FPR={c['v_fpr']:.4f}")
        print(f"Signal Triggers (TP): Pts={c['t_res']['signal_trigger_tp'][0]:.2f}, Hst={c['t_res']['signal_trigger_tp'][1]:.2f}, SR={c['t_res']['signal_trigger_tp'][2]:.2f}, FO={c['t_res']['signal_trigger_tp'][3]:.2f}")
        print()

    if not recon_candidates:
        print("No Recon configurations met the FPR and Recall constraints.")

    # ---------------------------------------------------------
    # LEGACY BASELINES
    # ---------------------------------------------------------
    print("==================================================")
    print("BASELINES")
    print("==================================================")
    # Legacy DDoS (packet_rate > 1000)
    ddos_tune_pr = df_ddos_tuning['packet_rate'].values
    ddos_val_pr = df_ddos_val['packet_rate'].values
    dtp = np.sum((ddos_tune_pr > 1000) & df_ddos_tuning['Is_Malicious'].values)
    dfp = np.sum((ddos_tune_pr > 1000) & ~df_ddos_tuning['Is_Malicious'].values)
    dtn = np.sum(~(ddos_tune_pr > 1000) & ~df_ddos_tuning['Is_Malicious'].values)
    dfn = np.sum(~(ddos_tune_pr > 1000) & df_ddos_tuning['Is_Malicious'].values)
    dprec, drec, df1, dfpr = compute_metrics(dtp, dfp, dtn, dfn)
    print(f"Legacy DDoS Tuning: F1={df1:.4f}, Recall={drec:.4f}, FPR={dfpr:.4f}")

    dtp = np.sum((ddos_val_pr > 1000) & df_ddos_val['Is_Malicious'].values)
    dfp = np.sum((ddos_val_pr > 1000) & ~df_ddos_val['Is_Malicious'].values)
    dtn = np.sum(~(ddos_val_pr > 1000) & ~df_ddos_val['Is_Malicious'].values)
    dfn = np.sum(~(ddos_val_pr > 1000) & df_ddos_val['Is_Malicious'].values)
    vprec, vrec, vf1, vfpr = compute_metrics(dtp, dfp, dtn, dfn)
    print(f"Legacy DDoS Valid:  F1={vf1:.4f}, Recall={vrec:.4f}, FPR={vfpr:.4f}")

    # Legacy Recon (ports > 50)
    recon_tune_p = df_recon_tuning['unique_destination_ports'].values
    recon_val_p = df_recon_val['unique_destination_ports'].values
    rtp = np.sum((recon_tune_p > 50) & df_recon_tuning['Is_Malicious'].values)
    rfp = np.sum((recon_tune_p > 50) & ~df_recon_tuning['Is_Malicious'].values)
    rtn = np.sum(~(recon_tune_p > 50) & ~df_recon_tuning['Is_Malicious'].values)
    rfn = np.sum(~(recon_tune_p > 50) & df_recon_tuning['Is_Malicious'].values)
    rprec, rrec, rf1, rfpr = compute_metrics(rtp, rfp, rtn, rfn)
    print(f"Legacy Recon Tuning: F1={rf1:.4f}, Recall={rrec:.4f}, FPR={rfpr:.4f}")

    rtp = np.sum((recon_val_p > 50) & df_recon_val['Is_Malicious'].values)
    rfp = np.sum((recon_val_p > 50) & ~df_recon_val['Is_Malicious'].values)
    rtn = np.sum(~(recon_val_p > 50) & ~df_recon_val['Is_Malicious'].values)
    rfn = np.sum(~(recon_val_p > 50) & df_recon_val['Is_Malicious'].values)
    vprec, vrec, vf1, vfpr = compute_metrics(rtp, rfp, rtn, rfn)
    print(f"Legacy Recon Valid:  F1={vf1:.4f}, Recall={vrec:.4f}, FPR={vfpr:.4f}")

if __name__ == '__main__':
    main()
