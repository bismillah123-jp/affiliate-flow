#!/usr/bin/env python3
"""flow_cli.py — pembungkus `gflow` CLI (https://github.com/swissmarley/gflow-cli).

npm: @swissmarley/gflow-cli (Node.js >= 20). Drive Google Flow dari terminal:
Nano Banana 2 (image) + Omni Flash (video), via Chrome milik sendiri.

Interface (v1.1.x):
  gflow image --id <id> --prompt <text> --model <name> --ratio <r>
              --out <dir> [--character n...] [--timeout s]
  gflow video --id <id> --prompt <text> --model <name> --ratio <r>
              --duration <s> --start-frame <p> [--end-frame <p>]
              --out <dir> [--character n...] [--timeout s]
  gflow character create --name <n> --prompt <t> --model <m> --image <p...>
  gflow character list
  gflow doctor

API shim (disengaja stabil supaya stage script tidak berubah):
  character_ensure(name, image, prompt) -> bool (True bila baru dibuat)
  image_generate(job_id, prompt, out_png, ...)      # Nano Banana 2
  video_generate(job_id, prompt, out_mp4, ...)      # Omni Flash (frames mode)

Konsistensi produk: foto katalog di-register sebagai Flow character
`aff-<slug>` (dibuat dari gambar katalog), lalu di-pass sebagai
--character di tiap generate image/video.

Mode dry-run (AFFILIATE_DRY_RUN=1): file dummy via Pillow/PyAV,
tanpa gflow / browser / kuota.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, is_dry_run, log, die, run, placeholder_png, placeholder_mp4  # noqa: E402

GFLOW_BIN = shutil.which("gflow") or "gflow"

# Nama Flow project: eksplisit > env GFLOW_PROJECT > "" (tanpa flag).
# Character itu project-scoped; kalau CLI gagal auto-create project
# ("No Flow project is open and one could not be created"), bikin project
# manual sekali di web Flow lalu pass --project <nama>.
def _project_name(explicit: str = "") -> str:
    return explicit or os.environ.get("GFLOW_PROJECT", "")


def _project_flag(explicit: str = "") -> list:
    name = _project_name(explicit)
    return ["--project", name] if name else []

_DRY_STATE = ROOT / ".dryrun_flow.json"


def _dry_state(data: dict | None = None) -> dict:
    if data is not None:
        _DRY_STATE.write_text(json.dumps(data))
        return data
    if _DRY_STATE.exists():
        return json.loads(_DRY_STATE.read_text())
    return {}


def _ratio(ratio: str) -> str:
    """Normalisasi rasio ke format Flow: '9x16' -> '9:16'."""
    r = ratio.strip().lower().replace("x", ":")
    return r


def _check_bin() -> None:
    if shutil.which("gflow") is None and not is_dry_run():
        die("perintah `gflow` tidak ditemukan.\n"
            "  Install: npm install -g @swissmarley/gflow-cli  (atau ./setup.sh)")


def _newest(outdir: Path, exts: tuple, prefer: str = "") -> Path | None:
    cands = [p for p in outdir.iterdir()
             if p.is_file() and p.suffix.lower() in exts]
    if not cands:
        return None
    if prefer:
        named = [p for p in cands if prefer in p.name]
        if named:
            cands = named
    return max(cands, key=lambda p: p.stat().st_mtime)


# ---------- character ----------

def _parse_character_list(stdout: str) -> list:
    names = []
    for line in stdout.splitlines():
        t = line.strip().lstrip("-*• ").strip()
        if t and not t.lower().startswith(("name", "character", "saved", "no ")):
            names.append(t.split()[0])
    return names


def character_exists(name: str) -> bool:
    if is_dry_run():
        return name in _dry_state().get("characters", [])
    r = subprocess.run([GFLOW_BIN, "character", "list"] + _project_flag(),
                       capture_output=True, text=True, timeout=120)
    return name in _parse_character_list(r.stdout)


def character_create_cmd(name: str, prompt: str, images: list,
                         model: str = "nano-banana-2",
                         project: str = "") -> list:
    cmd = [GFLOW_BIN, "character", "create",
           "--name", name,
           "--prompt", prompt,
           "--model", model]
    for img in images:
        cmd += ["--image", img]
    cmd += _project_flag(project)
    return cmd


def character_ensure(name: str, image: str, prompt: str,
                     headed: bool = False, project: str = "") -> bool:
    """Register foto katalog sebagai Flow character (identitas produk)."""
    if character_exists(name):
        log(f"character '{name}' sudah ada, skip")
        return False
    log(f"membuat character '{name}' dari {image}")
    if is_dry_run():
        st = _dry_state()
        chars = st.get("characters", [])
        chars.append(name)
        _dry_state({"characters": sorted(set(chars))})
        return True
    if not Path(image).exists():
        die(f"file gambar character tidak ada: {image}")
    cmd = character_create_cmd(name, prompt, [image], project=project)
    log("+ " + " ".join(cmd)[:160])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if r.returncode != 0:
        err = (r.stderr or "") + (r.stdout or "")
        print(err[-2000:])
        if "No Flow project" in err:
            die("gflow butuh Flow project yang kebuka dan auto-create-nya gagal.\n"
                "  Bikin project manual sekali di Flow web\n"
                "  (https://labs.google/fx/tools/flow, misal bernama 'affiliate-flow'),\n"
                "  lalu ulangi dengan:\n"
                "    python3 pipeline.py --auto --project affiliate-flow")
        die(f"gflow character create gagal (exit {r.returncode})")
    log(f"character tersimpan: {name}")
    return True


# ---------- image ----------

def image_cmd(job_id: str, prompt: str, out_dir: str,
              model: str = "Nano Banana 2", ratio: str = "9:16",
              character: str = "", timeout: int = 900,
              project: str = "") -> list:
    cmd = [GFLOW_BIN, "image",
           "--id", job_id,
           "--prompt", prompt,
           "--model", model,
           "--ratio", _ratio(ratio),
           "--out", out_dir,
           "--timeout", str(timeout)]
    if character:
        cmd += ["--character", character]
    cmd += _project_flag(project)
    return cmd


def image_generate(job_id: str, prompt: str, out_png: str,
                   model: str = "Nano Banana 2", ratio: str = "9:16",
                   character: str = "",
                   headed: bool = False, project: str = "",
                   timeout: int = 900) -> Path:
    """Generate 1 gambar 9:16 via Nano Banana 2 (+character produk)."""
    out = Path(out_png)
    if out.exists():
        log(f"{out.name} sudah ada, skip")
        return out
    if is_dry_run():
        log(f"[dry-run] gflow image --id {job_id} --model '{model}'")
        out.parent.mkdir(parents=True, exist_ok=True)
        return placeholder_png(out)

    _check_bin()
    if character and not character_exists(character):
        die(f"character '{character}' belum ada — jalankan tahap hd dulu")

    tmpdir = Path(tempfile.mkdtemp(prefix=f"aff-{job_id}-"))
    try:
        run(image_cmd(job_id, prompt, str(tmpdir), model, ratio,
                      character, timeout, project), timeout=timeout + 120)
        got = _newest(tmpdir, (".png", ".jpg", ".jpeg", ".webp"), prefer=job_id)
        if not got:
            die(f"gflow image tidak menghasilkan file untuk job {job_id}")
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(got), str(out))
        log(f"OK: {out.name}")
        return out
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


# ---------- video ----------

def video_cmd(job_id: str, prompt: str, out_dir: str,
              model: str = "Omni Flash", ratio: str = "9:16",
              duration: int = 10, start_frame: str = "",
              end_frame: str = "", character: str = "",
              timeout: int = 1800, project: str = "") -> list:
    cmd = [GFLOW_BIN, "video",
           "--id", job_id,
           "--prompt", prompt,
           "--model", model,
           "--ratio", _ratio(ratio),
           "--duration", str(duration),
           "--out", out_dir,
           "--timeout", str(timeout)]
    if start_frame:
        cmd += ["--start-frame", start_frame]
    if end_frame:
        cmd += ["--end-frame", end_frame]
    if character:
        cmd += ["--character", character]
    cmd += _project_flag(project)
    return cmd


def video_generate(job_id: str, prompt: str, out_mp4: str,
                   model: str = "Omni Flash", ratio: str = "9:16",
                   duration: int = 10, start_frame: str = "",
                   end_frame: str = "", character: str = "",
                   headed: bool = False, project: str = "",
                   timeout: int = 1800) -> Path:
    """Generate 1 video via Omni Flash (frames mode bila start_frame diisi)."""
    out = Path(out_mp4)
    if out.exists():
        log(f"{out.name} sudah ada, skip")
        return out
    if is_dry_run():
        log(f"[dry-run] gflow video --id {job_id} --model '{model}' "
            f"--duration {duration}")
        out.parent.mkdir(parents=True, exist_ok=True)
        return placeholder_mp4(out, duration=duration)

    _check_bin()
    if not start_frame:
        die("video butuh start_frame (storyboard scene01)")
    for f in (start_frame, end_frame):
        if f and not Path(f).exists():
            die(f"file frame tidak ada: {f}")

    tmpdir = Path(tempfile.mkdtemp(prefix=f"aff-{job_id}-"))
    try:
        run(video_cmd(job_id, prompt, str(tmpdir), model, ratio, duration,
                      start_frame, end_frame, character, timeout, project),
            timeout=timeout + 120)
        got = _newest(tmpdir, (".mp4",), prefer=job_id)
        if not got:
            die(f"gflow video tidak menghasilkan file untuk job {job_id}")
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(got), str(out))
        log(f"OK: {out.name}")
        return out
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
