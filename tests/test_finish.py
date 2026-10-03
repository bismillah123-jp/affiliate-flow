#!/usr/bin/env python3
"""test_finish.py — uji verifikasi finish.py + probe() tanpa ffmpeg."""
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

from common import probe, placeholder_mp4, placeholder_png  # noqa: E402


class TestProbe(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aff-probe-"))

    def test_probe_mp4_dummy(self):
        mp4 = placeholder_mp4(self.tmp / "t.mp4", duration=10)
        info = probe(mp4)
        self.assertTrue(info["ok"])
        self.assertIn("video", info["streams"])
        self.assertIn("audio", info["streams"])
        self.assertTrue(9.0 <= info["duration"] <= 11.0)
        self.assertEqual((info["width"], info["height"]), (576, 1024))

    def test_probe_png_terbaca_dimensi(self):
        # PyAV membuka PNG sebagai stream video (image2) — wajar;
        # yang penting probe tidak crash dan dimensinya kebaca
        png = placeholder_png(self.tmp / "t.png")
        info = probe(png)
        self.assertTrue(info["ok"])
        self.assertEqual((info["width"], info["height"]), (768, 1360))

    def test_probe_file_tidak_ada(self):
        info = probe(self.tmp / "tidak-ada.mp4")
        self.assertFalse(info["ok"])


class TestFinishStage(unittest.TestCase):
    def test_finish_dryrun(self):
        import subprocess
        repo = Path(__file__).resolve().parent.parent
        pdir = repo / "products" / "_testfinish"
        clips = pdir / "clips"
        clips.mkdir(parents=True, exist_ok=True)
        placeholder_mp4(clips / "final_10s.mp4", duration=10)
        env = dict(os.environ, AFFILIATE_DRY_RUN="1")
        r = subprocess.run(
            [sys.executable, str(repo / "lib" / "finish.py"),
             "--product", "_testfinish", "--dry-run"],
            capture_output=True, text=True, timeout=120, env=env)
        self.assertEqual(r.returncode, 0, r.stderr[-500:])
        self.assertTrue((pdir / "final.mp4").exists())
        # bersih-bersih
        import shutil
        shutil.rmtree(pdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
