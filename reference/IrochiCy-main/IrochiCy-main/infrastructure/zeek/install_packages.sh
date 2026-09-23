#!/usr/bin/env bash
# install_packages.sh — Run inside the Zeek container to install JA3/JA4 packages
# Usage: docker exec sih26145_zeek bash /usr/local/zeek/share/zeek/site/install_packages.sh
set -euo pipefail

echo "=== Installing Zeek Package Manager (zkg) ==="
pip3 install zkg

echo "=== Auto-configuring zkg ==="
zkg autoconfig

echo "=== Installing JA3 (v1.0.0) ==="
zkg install zeek/zeek-ja3 --version v1.0.0 --force

echo "=== Installing JA4 (v0.12.0) ==="
zkg install zeek/ja4 --version v0.12.0 --force

echo ""
echo "=== Installed Packages ==="
zkg list installed

echo ""
echo "=== Done ==="
