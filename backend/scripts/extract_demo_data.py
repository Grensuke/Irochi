import os
import csv
import json
import random
import time
from datetime import datetime, timedelta

DATA_DIR = r"C:\Users\STARK\Documents\Irochi-Data\CIC-IDS2017\MachineLearningCSV"
OUTPUT_FILE = r"C:\Users\STARK\Documents\Irochi\backend\data\real_demo_traffic.jsonl"

def clean_col(c):
    return c.strip().replace(" ", "")

# Define the sequence of attacks for the highlight reel
# Each tuple: (CSV_File, Target_Label, Attack_Src_Pool, Attack_Dst_Pool, Num_Benign, Num_Attack)
ATTACK_SCENARIOS = [
    (
        "Wednesday-workingHours.pcap_ISCX.csv",
        "DoS Hulk",
        ["198.51.100.10", "198.51.100.11"],
        ["10.0.0.5"],
        100, 100
    ),
    (
        "Friday-WorkingHours-Morning.pcap_ISCX.csv",
        "Bot",
        ["192.168.1.15"], # Compromised internal host
        ["198.51.100.99"], # External C2
        50, 50
    ),
    (
        "Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv",
        "PortScan",
        ["203.0.113.50"],
        [f"10.0.0.{i}" for i in range(1, 20)],
        100, 150
    ),
    (
        "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
        "DDoS",
        [f"botnet-{i}.attacker.com" for i in range(1, 50)],
        ["10.0.0.5"],
        100, 500
    )
]

def generate_canonical_event(row, headers, is_attack, scenario, current_ts):
    _, target_label, src_pool, dst_pool, _, _ = scenario
    
    # Assign IPs based on whether it's part of the attack or background noise
    if is_attack:
        src_ip = random.choice(src_pool)
        dst_ip = random.choice(dst_pool)
    else:
        src_ip = f"192.168.1.{random.randint(10, 50)}"
        dst_ip = f"10.0.0.{random.randint(1, 200)}"
        
    try:
        dst_port = int(row[headers.index("DestinationPort")])
    except:
        dst_port = 443

    payload = {}
    
    # Safely map orig/resp bytes/pkts if possible, else defaults
    try:
        orig_bytes = int(row[headers.index("TotalLengthofFwdPackets")])
        resp_bytes = int(row[headers.index("TotalLengthofBwdPackets")])
        orig_pkts = int(row[headers.index("TotalFwdPackets")])
        resp_pkts = int(row[headers.index("TotalBackwardPackets")])
    except:
        orig_bytes, resp_bytes, orig_pkts, resp_pkts = 100, 200, 1, 1

    if is_attack:
        # Dramatically inflate packets and bytes to guarantee threshold breaches for the demo
        orig_pkts *= 100
        orig_bytes *= 100
        if "DDoS" in target_label or "DoS" in target_label:
            orig_pkts = max(orig_pkts, 5000)
            orig_bytes = max(orig_bytes, 5000000)
        elif "PortScan" in target_label:
            dst_port = random.randint(1, 1024) # Ensure varying ports for recon

    payload.update({
        "orig_bytes": orig_bytes,
        "resp_bytes": resp_bytes,
        "orig_pkts": orig_pkts,
        "resp_pkts": resp_pkts,
        "conn_state": "SF",
        "history": "ShADadFf",
        # Including all the ML features so the detectors can evaluate them
    })
    
    # Pack the remaining features that ML models expect
    for i, col in enumerate(headers):
        if col not in ["DestinationPort", "Label"]:
            try:
                payload[col] = float(row[i])
            except:
                pass
                
    event = {
        "event_id": f"evt-{int(current_ts)}-{random.randint(1000, 9999)}",
        "connection_id": f"conn-{src_ip}-{dst_ip}-{random.randint(1000,9999)}",
        "timestamp": int(current_ts * 1000000),
        "timestamp_precision": "microsecond",
        "ingest_timestamp": int(time.time() * 1000000),
        "sensor_source": "zeek",
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "src_port": random.randint(1024, 65535),
        "dst_port": dst_port,
        "protocol": "tcp",
        "schema_version": "1.0.0",
        "event_type": "connection",
        "payload": payload
    }
    return event

def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Start simulating from "now"
    current_ts = time.time()
    events = []
    
    for scenario in ATTACK_SCENARIOS:
        csv_file, target_label, src_pool, dst_pool, num_benign, num_attack = scenario
        filepath = os.path.join(DATA_DIR, csv_file)
        print(f"Processing {csv_file} (Target: {target_label})...")
        
        if not os.path.exists(filepath):
            print(f"WARNING: Missing file {filepath}. Skipping.")
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            raw_headers = next(reader)
            headers = [clean_col(h) for h in raw_headers]
            
            label_idx = headers.index("Label")
            
            benign_rows = []
            attack_rows = []
            
            for row in reader:
                if not row or len(row) <= label_idx:
                    continue
                lbl = row[label_idx].strip()
                if lbl == "BENIGN" and len(benign_rows) < num_benign * 10:
                    benign_rows.append(row)
                elif lbl == target_label and len(attack_rows) < num_attack * 5:
                    attack_rows.append(row)
                    
                if len(benign_rows) >= num_benign * 10 and len(attack_rows) >= num_attack * 5:
                    break
                    
        # Sample to requested amounts
        b_sample = random.sample(benign_rows, min(len(benign_rows), num_benign))
        a_sample = random.sample(attack_rows, min(len(attack_rows), num_attack))
        
        print(f"  Extracted {len(b_sample)} BENIGN and {len(a_sample)} {target_label} flows.")
        
        # Interleave them over a short time window (e.g. 60 seconds for this scenario)
        scenario_events = []
        for r in b_sample:
            scenario_events.append((generate_canonical_event(r, headers, False, scenario, 0), "benign"))
        for r in a_sample:
            scenario_events.append((generate_canonical_event(r, headers, True, scenario, 0), "attack"))
            
        random.shuffle(scenario_events)
        
        # Assign increasing timestamps
        for i, (evt, _type) in enumerate(scenario_events):
            if _type == "attack":
                current_ts += 0.001 # 1000 events per second for attacks (highly clustered)
            else:
                current_ts += 0.1 # 10 events per second for benign
            evt["timestamp"] = int(current_ts * 1000000)
            events.append(evt)
            
        # Add a 5 second pause between scenarios
        current_ts += 5.0
        
    print(f"Writing {len(events)} total events to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        for evt in events:
            out.write(json.dumps(evt) + "\n")
            
    print("Done! Tape is ready.")

if __name__ == "__main__":
    main()
