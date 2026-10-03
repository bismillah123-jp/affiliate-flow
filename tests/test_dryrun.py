#!/usr/bin/env python3
"""test_dryrun.py — uji end-to-end pipeline dalam mode --dry-run.

Tidak butuh: API key, browser, login Google, kuota Flow, network,
ffmpeg, maupun TTS. Semua dummy dibuat via Pillow/PyAV.
"""
import json
import os
import shutil
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "lib"))


class TestDryRun(unittest.TestCase):
    def test_full_pipeline_dryrun(self):
        env = dict(os.environ, AFFILIATE_DRY_RUN="1")
        r = subprocess.run(
            [sys.executable, os.path.join(ROOT, "pipeline.py"),
             "--manual-name", "Sabun Viral Tes", "--dry-run"],
            capture_output=True, text=True, timeout=900, env=env, cwd=ROOT)
        # slug berasal dari slugify("Sabun Viral Tes")
        slug = "sabun-viral-tes"
        pdir = os.path.join(ROOT, "products", slug)
        self.assertEqual(r.returncode, 0,
                         f"pipeline dry-run gagal:\n{r.stdout[-3000:]}\n{r.stderr[-2000:]}")
        expected = [
            "research.json",
            "images/img1.png", "images/manifest.json",
            "hd/img1_hd.png",
            "storyboard.json",
            "storyboard/scene01.png", "storyboard/scene02.png",
            "storyboard/scene03.png",
            "clips/final_10s.mp4",
            "final.mp4",   # tanpa vo/ — VO sudah bawaan di video
        ]
        for rel in expected:
            p = os.path.join(pdir, rel)
            self.assertTrue(os.path.exists(p), f"hilang: {rel}")
            self.assertGreater(os.path.getsize(p), 0, f"kosong: {rel}")

        # storyboard.json valid & total 10 dtk
        sb = json.load(open(os.path.join(pdir, "storyboard.json")))
        self.assertEqual(sb["total_seconds"], 10)

        # final.mp4 punya stream video+audio, durasi ~10 dtk (via PyAV)
        from common import probe
        info = probe(os.path.join(pdir, "final.mp4"))
        self.assertTrue(info["ok"])
        self.assertTrue(8.0 <= info["duration"] <= 12.0,
                        f"durasi aneh: {info['duration']}")
        self.assertIn("video", info["streams"])
        self.assertIn("audio", info["streams"])

        shutil.rmtree(pdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
