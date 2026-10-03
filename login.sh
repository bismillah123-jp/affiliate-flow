#!/bin/bash
# login.sh — login Google Flow (minimal).
# Memakai `gflow` CLI dari https://github.com/ffroliva/gflow-cli.
# Sesi/profil di ~/.local/share/gflow-cli (atau $GFLOW_CLI_HOME bila di-set).
set -e
cd "$(dirname "$0")"

need_gflow() {
  command -v gflow >/dev/null || {
    echo "✘ perintah 'gflow' belum diinstall."
    echo "  Install: pip install gflow-cli  (atau ./setup.sh)"
    exit 1
  }
}

case "${1:-}" in
  --check)
    need_gflow
    gflow doctor >/dev/null 2>&1 \
      && echo "✔ Sesi valid. Pipeline siap jalan." \
      || { echo "✘ Sesi belum valid. Jalankan: ./login.sh"; exit 1; } ;;
  --credits)
    need_gflow
    gflow credits user ;;
  *)
    need_gflow
    echo "== login Google Flow =="
    echo "Browser kebuka — selesaikan login Google di sana."
    gflow auth login
    echo ""
    gflow doctor >/dev/null 2>&1 \
      && echo "✔ Login OK, sesi valid." \
      || echo "⚠ Login selesai tapi doctor gagal — cek manual: gflow doctor" ;;
esac
