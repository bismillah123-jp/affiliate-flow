#!/bin/bash
# setup.sh — siapkan pipeline video affiliate di Linux manapun (sekali aja).
# Membuat venv .venv, install gflow-cli (ffroliva) + dependensi + browser.
# TANPA ffmpeg, TANPA TTS pihak ketiga — semua dari pip.
set -e
cd "$(dirname "$0")"

echo "== cek python3 =="; python3 --version

echo "== buat venv .venv =="
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
echo "== install dependensi python =="
.venv/bin/pip install -r requirements.txt

echo "== install browser untuk gflow-cli (chromium) =="
.venv/bin/python -m playwright install chromium --with-deps 2>/dev/null \
  || .venv/bin/python -m playwright install chromium

echo ""
echo "SELESAI ✔ (tanpa ffmpeg, tanpa TTS pihak ketiga)"
echo ""
echo "Langkah terakhir (sekali aja per mesin):"
echo "  .venv/bin/python pipeline.py --auth   # login Google Flow (= gflow auth login)"
echo ""
echo "Lalu jalan:  .venv/bin/python pipeline.py --auto --dry-run   # uji tanpa kuota"
echo "             .venv/bin/python pipeline.py --auto              # produksi"
