#!/usr/bin/env python3
"""common.py — utilitas bersama pipeline affiliate.

TANPA ffmpeg: semua operasi media memakai pustaka Python murni
(Pillow untuk gambar, PyAV untuk video) — tidak butuh binary sistem.

Semua path relatif terhadap ROOT (folder repo), jadi jalan di Linux manapun.
Mode dry-run: set env AFFILIATE_DRY_RUN=1 (atau --dry-run di pipeline.py).
"""
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def is_dry_run() -> bool:
    return os.environ.get("AFFILIATE_DRY_RUN", "") == "1"


def log(msg: str) -> None:
    print(f"[aff] {msg}", flush=True)


def die(msg: str, code: int = 1) -> "NoReturn":  # type: ignore[name-defined]
    print(f"[aff] FATAL: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


def run(cmd, check: bool = True, timeout: int = 900, **kw):
    """Jalankan subprocess dengan logging. cmd = list[str]."""
    printable = " ".join(str(c) for c in cmd)
    log(f"+ {printable[:160]}")
    try:
        r = subprocess.run(cmd, timeout=timeout, **kw)
    except FileNotFoundError:
        die(f"perintah tidak ditemukan: {cmd[0]}")
    if check and r.returncode != 0:
        die(f"perintah gagal (exit {r.returncode}): {printable[:120]}")
    return r


def product_dir(slug: str) -> Path:
    d = ROOT / "products" / slug
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def save_json(path: Path, obj) -> None:
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "produk"


# ---------------------------------------------------------------------------
# Media tanpa ffmpeg
# ---------------------------------------------------------------------------
def placeholder_png(path: Path, w: int = 768, h: int = 1360) -> Path:
    """Bikin PNG dummy valid pakai Pillow (untuk dry-run)."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (w, h), (30, 30, 40))
    d = ImageDraw.Draw(img)
    d.rectangle([w // 4, h // 4, 3 * w // 4, 3 * h // 4], outline=(200, 200, 200))
    d.text((w // 4 + 10, h // 2), "dry-run", fill=(200, 200, 200))
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path)
    return path


def placeholder_mp4(path: Path, duration: int = 10, w: int = 576, h: int = 1024,
                    with_audio: bool = True) -> Path:
    """Bikin MP4 dummy valid (video + audio) pakai PyAV (untuk dry-run)."""
    import av
    import numpy as np
    from fractions import Fraction
    path.parent.mkdir(parents=True, exist_ok=True)
    fps = 30
    total = fps * duration
    with av.open(str(path), "w") as out:
        vs = out.add_stream("mpeg4", rate=fps)
        vs.width, vs.height, vs.pix_fmt = w, h, "yuv420p"
        vs.time_base = Fraction(1, fps)
        # PENTING: kedua stream harus dibuat di awal sebelum encode,
        # kalau tidak muxer crash (SIGFPE) saat stream audio ditambah belakangan.
        aus = None
        sr = 44100
        if with_audio:
            aus = out.add_stream("aac", rate=sr)
            aus.time_base = Fraction(1, sr)
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:, :, 0] = 40  # pola sederhana biar tidak hitam total
        for i in range(total):
            f = av.VideoFrame.from_ndarray(frame, format="rgb24")
            f.pts = i
            f.time_base = Fraction(1, fps)
            for p in vs.encode(f):
                out.mux(p)
        for p in vs.encode():
            out.mux(p)
        if aus is not None:
            n = sr * duration
            t = np.arange(n, dtype=np.float32) / sr
            tone = (0.3 * np.sin(2 * math.pi * 440 * t)).astype(np.float32)
            pcm = (tone * 32767).astype(np.int16)
            step = 1024
            for i in range(0, n, step):
                chunk = pcm[i:i + step]
                af = av.AudioFrame.from_ndarray(
                    chunk.reshape(1, -1), format="s16", layout="mono")
                af.sample_rate = sr
                af.pts = i
                af.time_base = Fraction(1, sr)
                for p in aus.encode(af):
                    out.mux(p)
            for p in aus.encode():
                out.mux(p)
    return path


def probe(path: Path) -> dict:
    """Info media via PyAV: {duration, width, height, streams:[...], ok}.

    Pengganti ffprobe — tanpa binary ffmpeg.
    """
    import av
    info: dict = {"duration": 0.0, "width": 0, "height": 0,
                  "streams": [], "ok": False}
    try:
        with av.open(str(path)) as c:
            if c.duration:
                info["duration"] = float(c.duration) / 1_000_000
            for s in c.streams:
                info["streams"].append(s.type)
                if s.type == "video":
                    info["width"] = s.width or 0
                    info["height"] = s.height or 0
                    if not info["duration"] and s.duration and s.time_base:
                        info["duration"] = float(s.duration * s.time_base)
            info["ok"] = True
    except Exception as e:
        log(f"probe gagal: {e}")
    return info
