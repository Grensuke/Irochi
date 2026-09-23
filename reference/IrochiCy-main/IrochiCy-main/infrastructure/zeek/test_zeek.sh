#!/usr/bin/env bash
# test_zeek.sh — Smoke test for Zeek inside the container
# Usage: docker exec sih26145_zeek bash /usr/local/zeek/share/zeek/site/test_zeek.sh
set -euo pipefail

echo "=== Zeek Version ==="
zeek --version

echo ""
echo "=== Running sample PCAP ==="

# Find a test PCAP (Zeek ships with some)
PCAP=""
for candidate in /pcaps/zeek_samples/*.pcap /pcaps/*.pcap; do
    if [ -f "$candidate" ]; then
        PCAP="$candidate"
        break
    fi
done

if [ -z "$PCAP" ]; then
    echo "ERROR: No PCAP files found in /pcaps/ or /pcaps/zeek_samples/"
    echo "Run download_pcaps.sh first."
    exit 1
fi

echo "Using PCAP: $PCAP"
cd /tmp
rm -f conn.log dns.log ssl.log

zeek -r "$PCAP" /usr/local/zeek/share/zeek/site/local.zeek 2>&1 || true

echo ""
echo "=== Generated Log Files ==="
ls -la /tmp/*.log 2>/dev/null || echo "No log files generated"

echo ""
echo "=== Checking JA3 ==="
if [ -f /tmp/ssl.log ]; then
    if grep -q "ja3" /tmp/ssl.log 2>/dev/null; then
        echo "JA3: PRESENT"
    else
        echo "JA3: NOT FOUND (ssl.log exists but no ja3 field)"
    fi
else
    echo "JA3: NOT TESTED (no ssl.log — PCAP may not contain TLS traffic)"
fi

echo ""
echo "=== Checking conn.log ==="
if [ -f /tmp/conn.log ]; then
    LINE_COUNT=$(grep -cv "^#" /tmp/conn.log 2>/dev/null || echo "0")
    echo "conn.log: $LINE_COUNT data rows"
else
    echo "conn.log: NOT FOUND"
fi

echo ""
echo "=== Smoke Test Complete ==="
