#!/bin/bash
# login.sh — login Google Flow (minimal).
# Memakai `gflow` CLI dari https://github.com/swissmarley/gflow-cli
# (npm: @swissmarley/gflow-cli). Sesi/profil disimpan di .gflow/profiles/<name>.
set -e
cd "$(dirname "$0")"

need_gflow() {
  command -v gflow >/dev/null || {
    echo "✘ perintah 'gflow' belum diinstall."
    echo "  Install: npm install -g @swissmarley/gflow-cli  (atau ./setup.sh)"
    exit 1
  }
}

case "${1:-}" in
  --check)
    need_gflow
    gflow doctor >/dev/null 2>&1 \
      && echo "✔ Sesi valid. Pipeline siap jalan." \
      || { echo "✘ Sesi belum valid. Jalankan: ./login.sh"; exit 1; } ;;
  *)
    need_gflow
    echo "== login Google Flow =="
    echo "Chrome kebuka — selesaikan login Google di sana."
    gflow auth login
    echo ""
    gflow doctor >/dev/null 2>&1 \
      && echo "✔ Login OK, sesi valid." \
      || echo "⚠ Login selesai tapi doctor gagal — cek manual: gflow doctor" ;;
esac
