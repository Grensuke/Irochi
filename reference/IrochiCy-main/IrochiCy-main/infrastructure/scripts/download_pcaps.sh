#!/usr/bin/env bash
# download_pcaps.sh — Download public PCAP datasets for Zeek analysis
# Run from the infrastructure/ directory
set -euo pipefail

PCAP_DIR="./pcaps"

echo "=== Creating PCAP directories ==="
mkdir -p "$PCAP_DIR"/{zeek_samples,ctu13,dga_dns,cicids2017}

echo ""
echo "=== Downloading CTU-13 Scenario 1 — Neris Botnet (~50MB) ==="
echo "    (C2 beaconing, exfiltration, IRC-based botnet)"
if [ ! -f "$PCAP_DIR/ctu13/scenario1.pcap" ]; then
    curl -L --progress-bar -o "$PCAP_DIR/ctu13/scenario1.pcap" \
        "https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-48/botnet-capture-20110816-neris.pcap"
    echo "    Downloaded: scenario1.pcap"
else
    echo "    Already exists: scenario1.pcap"
fi

echo ""
echo "=== Downloading CTU-13 DGA Sample — DNS Tunneling / DGA ==="
if [ ! -f "$PCAP_DIR/dga_dns/dga_sample.pcap" ]; then
    curl -L --progress-bar -o "$PCAP_DIR/dga_dns/dga_sample.pcap" \
        "https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-42/botnet-capture-20110816-qvod.pcap"
    echo "    Downloaded: dga_sample.pcap"
else
    echo "    Already exists: dga_sample.pcap"
fi

echo ""
echo "=== Copying Zeek built-in test PCAPs ==="
docker exec sih26145_zeek bash -c \
    "find /usr/local/zeek -name '*.pcap' 2>/dev/null | head -5 | xargs -I{} cp {} /pcaps/zeek_samples/" \
    2>/dev/null || echo "    Zeek container not running — skipping built-in PCAPs"

echo ""
echo "=== CICIDS2017 (Manual Download Required) ==="
echo "    URL: https://www.unb.ca/cic/datasets/ids-2017.html"
echo "    Download: Wednesday-workingHours.pcap"
echo "    Save to:  $PCAP_DIR/cicids2017/"

echo ""
echo "=== PCAP Directory Contents ==="
find "$PCAP_DIR" -type f -name "*.pcap" -exec ls -lh {} \; 2>/dev/null || echo "No PCAPs found yet"

echo ""
echo "=== Done ==="
