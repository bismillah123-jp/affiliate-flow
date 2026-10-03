#!/usr/bin/env python3
"""finish.py — finalisasi video affiliate (tahap 6).

Video dari Omni Flash SUDAH berisi audio + voice-over Bahasa Indonesia
yang dibakar saat generate (tanpa TTS pihak ketiga, tanpa ffmpeg).

Tahap ini hanya:
  1. Verifikasi clips/final_10s.mp4 via PyAV
     (durasi ~10 dtk, ada stream video+audio, rasio 9:16)
  2. Salin ke products/<slug>/final.mp4 (siap upload TikTok/Shopee)

Usage: finish.py --product <slug> [--dry-run]
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import is_dry_run, log, die, product_dir, probe  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Finalisasi video (verifikasi)")
    ap.add_argument("--product", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        os.environ["AFFILIATE_DRY_RUN"] = "1"

    pdir = product_dir(a.product)
    clip = pdir / "clips" / "final_10s.mp4"
    if not clip.exists():
        die("clips/final_10s.mp4 tidak ada; jalankan tahap video dulu")

    info = probe(clip)
    if not info["ok"]:
        die(f"probe gagal untuk {clip.name}")
    dur = info["duration"]
    streams = info["streams"]
    w, h = info["width"], info["height"]
    log(f"clip: {dur:.1f} dtk | streams: {streams} | {w}x{h} | "
        f"{clip.stat().st_size // 1024} KB")

    problems = []
    if "video" not in streams:
        problems.append("tidak ada stream video")
    if "audio" not in streams:
        problems.append("tidak ada stream audio (VO bawaan hilang?)")
    if not (8.0 <= dur <= 12.0):
        problems.append(f"durasi {dur:.1f} dtk (harusnya ~10 dtk)")
    if w and h and abs(w / h - 9 / 16) > 0.05:
        problems.append(f"rasio {w}x{h} bukan 9:16")
    if problems:
        die("verifikasi gagal: " + "; ".join(problems))

    final = pdir / "final.mp4"
    shutil.copy(clip, final)
    log(f"final.mp4 OK ✔ -> {final}")
    log("tahap finish selesai ✔")


if __name__ == "__main__":
    main()
