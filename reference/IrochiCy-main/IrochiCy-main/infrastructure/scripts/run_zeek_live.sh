#!/usr/bin/env bash
# run_zeek_live.sh — Run Zeek in live capture mode on a network interface
# Usage: ./run_zeek_live.sh [interface]
# Defaults to eth0
set -euo pipefail

INTERFACE="${1:-eth0}"
OUTPUT_DIR="/zeek-logs/live"

echo "=== Zeek Live Capture ==="
echo "    Interface: $INTERFACE"
echo "    Output:    $OUTPUT_DIR"
echo ""
echo "    Press Ctrl+C to stop capture."
echo ""

docker exec -it sih26145_zeek bash -c "
    mkdir -p '$OUTPUT_DIR'
    cd '$OUTPUT_DIR'
    exec zeek -i '$INTERFACE' /usr/local/zeek/share/zeek/site/local.zeek
"
