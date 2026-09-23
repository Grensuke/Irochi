#!/usr/bin/env bash
# run_zeek_offline.sh — Run Zeek in offline mode against a PCAP file
# Usage: ./run_zeek_offline.sh [path-to-pcap]
# Defaults to CTU-13 Scenario 1 if no argument provided
set -euo pipefail

PCAP_FILE="${1:-/pcaps/ctu13/scenario1.pcap}"
OUTPUT_DIR="/zeek-logs/offline-$(date +%Y%m%d-%H%M%S)"

echo "=== Zeek Offline Analysis ==="
echo "    PCAP:   $PCAP_FILE"
echo "    Output: $OUTPUT_DIR"
echo ""

docker exec sih26145_zeek bash -c "
    mkdir -p '$OUTPUT_DIR'
    cd '$OUTPUT_DIR'
    zeek -r '$PCAP_FILE' /usr/local/zeek/share/zeek/site/local.zeek 2>&1
    echo ''
    echo '=== Generated Logs ==='
    ls -lh '$OUTPUT_DIR'/*.log 2>/dev/null || echo 'No logs generated'
    echo ''
    echo '=== Row Counts ==='
    for f in '$OUTPUT_DIR'/*.log; do
        if [ -f \"\$f\" ]; then
            COUNT=\$(grep -cv '^#' \"\$f\" 2>/dev/null || echo 0)
            echo \"  \$(basename \$f): \$COUNT rows\"
        fi
    done
"

echo ""
echo "=== Offline analysis complete ==="
echo "    Logs available at: $OUTPUT_DIR (inside zeek container)"
echo "    Access via: docker exec sih26145_zeek ls $OUTPUT_DIR"
