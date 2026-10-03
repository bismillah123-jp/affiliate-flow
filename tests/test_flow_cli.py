#!/usr/bin/env python3
"""test_flow_cli.py — uji lib/flow_cli.py dalam mode dry-run.

Tanpa gflow / browser / kuota: semua generate dipalsukan jadi file dummy.
Command builder (image_cmd/video_cmd/character_create_cmd) diuji sebagai
fungsi murni — memastikan flag cocok dengan CLI swissmarley/gflow-cli.
"""
import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["AFFILIATE_DRY_RUN"] = "1"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

import flow_cli as fc  # noqa: E402


class TestFlowCliDryRun(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aff-flow-"))

    def test_character_ensure_idempotent(self):
        fc.character_ensure("aff-tes2", "/tmp/x.png", "prompt")
        self.assertTrue(fc.character_exists("aff-tes2"))
        # kedua kali: sudah ada -> return False
        self.assertFalse(fc.character_ensure("aff-tes2", "/tmp/x.png", "prompt"))

    def test_image_generate_dummy(self):
        out = self.tmp / "scene01.png"
        got = fc.image_generate("job-1", "prompt tes", str(out),
                                model="Nano Banana 2")
        self.assertTrue(got.exists())
        self.assertGreater(got.stat().st_size, 0)
        mtime = got.stat().st_mtime
        got2 = fc.image_generate("job-1", "prompt lain", str(out))
        self.assertEqual(got2.stat().st_mtime, mtime)

    def test_video_generate_dummy_10s(self):
        out = self.tmp / "final_10s.mp4"
        got = fc.video_generate("job-v", "prompt video", str(out),
                                model="Omni Flash", duration=10,
                                start_frame=str(self.tmp / "s.png"))
        # dry-run: start_frame tidak dicek ketat
        self.assertTrue(got.exists())
        self.assertGreater(got.stat().st_size, 0)


class TestFlowCliCmd(unittest.TestCase):
    def test_ratio_normalize(self):
        self.assertEqual(fc._ratio("9x16"), "9:16")
        self.assertEqual(fc._ratio("9:16"), "9:16")
        self.assertEqual(fc._ratio("16x9"), "16:9")

    def test_image_cmd_flags(self):
        cmd = fc.image_cmd("job-x", "prompt", "/tmp/out",
                           model="Nano Banana 2", ratio="9x16",
                           character="aff-p")
        self.assertEqual(cmd[:2], [fc.GFLOW_BIN, "image"])
        self.assertIn("--id", cmd)
        self.assertIn("job-x", cmd)
        self.assertIn("--prompt", cmd)
        self.assertIn("--model", cmd)
        self.assertIn("Nano Banana 2", cmd)
        self.assertIn("--ratio", cmd)
        self.assertIn("9:16", cmd)          # ternormalisasi
        self.assertNotIn("9x16", cmd)
        self.assertIn("--out", cmd)
        self.assertIn("--character", cmd)
        self.assertIn("aff-p", cmd)
        # tanpa subcommand i2i/t2i (CLI swissmarley: gflow image langsung)
        self.assertNotIn("i2i", cmd)
        self.assertNotIn("t2i", cmd)

    def test_video_cmd_flags(self):
        cmd = fc.video_cmd("job-v", "prompt", "/tmp/out",
                           model="Omni Flash", ratio="9:16",
                           duration=10, start_frame="/tmp/a.png",
                           end_frame="/tmp/b.png", character="aff-p")
        self.assertEqual(cmd[:2], [fc.GFLOW_BIN, "video"])
        self.assertIn("--id", cmd)
        self.assertIn("--prompt", cmd)
        self.assertIn("--duration", cmd)
        self.assertIn("10", cmd)
        self.assertIn("--start-frame", cmd)
        self.assertIn("/tmp/a.png", cmd)
        self.assertIn("--end-frame", cmd)
        self.assertIn("--character", cmd)
        self.assertNotIn("i2v", cmd)
        self.assertNotIn("--initial-frame", cmd)

    def test_character_create_cmd_flags(self):
        cmd = fc.character_create_cmd("aff-p", "desc", ["/tmp/a.png"])
        self.assertEqual(cmd[:3], [fc.GFLOW_BIN, "character", "create"])
        self.assertIn("--name", cmd)
        self.assertIn("aff-p", cmd)
        self.assertIn("--prompt", cmd)
        self.assertIn("--image", cmd)
        self.assertIn("/tmp/a.png", cmd)

    def test_parse_character_list(self):
        names = fc._parse_character_list("aff-pembersih-noda\naff-lain\n")
        self.assertIn("aff-pembersih-noda", names)


if __name__ == "__main__":
    unittest.main()
