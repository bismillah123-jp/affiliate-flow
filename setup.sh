#!/bin/bash
# setup.sh — siapkan pipeline video affiliate di Linux manapun (sekali aja).
# Membuat venv .venv (dependensi Python) + install gflow CLI (swissmarley, npm).
# TANPA ffmpeg, TANPA TTS pihak ketiga.
set -e
cd "$(dirname "$0")"

echo "== cek python3 & node =="; python3 --version
command -v node >/dev/null || { echo "✘ node belum ada — install Node.js >= 20 dulu (https://nodejs.org)"; exit 1; }
node --version; npm --version

echo "== buat venv .venv =="
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
echo "== install dependensi python =="
.venv/bin/pip install -r requirements.txt

echo "== install gflow CLI (@swissmarley/gflow-cli) =="
if command -v gflow >/dev/null; then
  echo "gflow sudah ada: $(gflow --version)"
else
  npm install -g @swissmarley/gflow-cli
fi

echo ""
echo "SELESAI ✔ (tanpa ffmpeg, tanpa TTS pihak ketiga)"
echo "CATATAN: gflow butuh Google Chrome asli (bukan chromium) + login Google Flow."
echo ""
echo "Langkah terakhir (sekali aja per mesin):"
echo "  .venv/bin/python pipeline.py --auth   # login Google Flow (= gflow auth login)"
echo ""
echo "Lalu jalan:  .venv/bin/python pipeline.py --auto --dry-run   # uji tanpa kuota"
echo "             .venv/bin/python pipeline.py --auto              # produksi"
