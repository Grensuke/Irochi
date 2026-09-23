#!/usr/bin/env bash
# verify_topics.sh — Create and verify all 6 Redpanda topics for SIH26145
# Run from any directory. Requires sih26145_redpanda container to be running.
set -euo pipefail

RPK="docker exec sih26145_redpanda rpk"

echo "=== Creating Redpanda Topics ==="

echo "  Creating canonical.connection (4 partitions, 1h retention)..."
$RPK topic create canonical.connection \
    --partitions 4 \
    --topic-config retention.ms=3600000 \
    2>/dev/null || echo "    (already exists)"

echo "  Creating canonical.dns (4 partitions, 1h retention)..."
$RPK topic create canonical.dns \
    --partitions 4 \
    --topic-config retention.ms=3600000 \
    2>/dev/null || echo "    (already exists)"

echo "  Creating canonical.tls (2 partitions, 1h retention)..."
$RPK topic create canonical.tls \
    --partitions 2 \
    --topic-config retention.ms=3600000 \
    2>/dev/null || echo "    (already exists)"

echo "  Creating detector.results (2 partitions, 2h retention)..."
$RPK topic create detector.results \
    --partitions 2 \
    --topic-config retention.ms=7200000 \
    2>/dev/null || echo "    (already exists)"

echo "  Creating dead.letter (1 partition, 24h retention)..."
$RPK topic create dead.letter \
    --partitions 1 \
    --topic-config retention.ms=86400000 \
    2>/dev/null || echo "    (already exists)"

echo "  Creating pipeline.metrics (1 partition, 1h retention)..."
$RPK topic create pipeline.metrics \
    --partitions 1 \
    --topic-config retention.ms=3600000 \
    2>/dev/null || echo "    (already exists)"

echo ""
echo "=== Topic List ==="
$RPK topic list

echo ""
echo "=== Topic Details ==="
for topic in canonical.connection canonical.dns canonical.tls detector.results dead.letter pipeline.metrics; do
    echo ""
    echo "--- $topic ---"
    $RPK topic describe "$topic" 2>/dev/null | head -10 || echo "  (not found)"
done

echo ""
echo "=== Done ==="
