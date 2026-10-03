# 🎬 Affiliate Flow — video affiliate TikTok/Shopee otomatis

Bikin video affiliate vertikal 9:16 (±10 detik, voice-over Bahasa Indonesia
**bawaan**) otomatis dari riset produk sampai file final — pakai
[`gflow-cli`](https://github.com/ffroliva/gflow-cli) (Nano Banana 2 + Omni Flash).

**Tanpa ffmpeg. Tanpa TTS pihak ketiga.** Semua dependensi dari pip.

```
riset → images → hd → storyboard → video → finish
  1       2       3        4          5       6
```

| Tahap | Kerja | Teknologi |
|---|---|---|
| 1. `research` | Riset produk viral / FYP-potential | kurasi `data/trending_id.json`, manual, atau Google Trends |
| 2. `images` | Download gambar katalog produk | DuckDuckGo Images (`ddgs`, tanpa API key) |
| 3. `hd` | HD-kan + perjelas produk, buang background berantakan | Nano Banana 2 via `gflow image i2i --ref` |
| 4. `storyboard` | Storyboard **berupa gambar** (3 scene, total 10 dtk) | Nano Banana 2 via `gflow image t2i --ref` |
| 5. `video` | Storyboard → video 10 dtk beneran (bukan slideshow), **audio + VO Indonesia dibakar saat generate** | Omni Flash via `gflow video i2v` (frames mode) |
| 6. `finish` | Verifikasi (durasi, stream video+audio, 9:16) → `final.mp4` | PyAV (tanpa ffmpeg) |

## ✨ Aturan kualitas (dijaga pipeline)

- **Hanya tangan / POV tangan**, tidak ada wajah — di semua prompt visual.
- **Bahasa Indonesia** untuk voice-over (dibakar ke video oleh Omni Flash).
- **Anti-anomali**: `ANOMALY_GUARD` ditempel di setiap prompt
  (tangan anatomis benar — tepat 2 tangan, 5 jari per tangan, tanpa
  anggota tubuh ekstra, tanpa morphing).
- **Konsisten**: referensi visual `aff-<slug>` di-pass sebagai `--ref`
  di setiap generate; kemasan produk pixel-identical.
- Teks di video: tidak ada (disarankan) — "jangan terlalu rame teks".

## 🚀 Mulai

```bash
git clone <repo-ini> && cd affiliate-flow
./setup.sh
# login sekali:
.venv/bin/python pipeline.py --auth     # = gflow auth login
# atau: ./login.sh

# uji tanpa kuota:
.venv/bin/python pipeline.py --auto --dry-run
# produksi:
.venv/bin/python pipeline.py --auto
```

Butuh: Python 3.10+, akun Google dengan akses Google Flow (+ kuota generate).
Tidak butuh: ffmpeg sistem, API key TTS, API key gambar.

Perintah berguna:

```bash
.venv/bin/python pipeline.py --product <slug> --from hd   # lanjut dari tahap hd
.venv/bin/python pipeline.py --product <slug> --only video
.venv/bin/python pipeline.py --manual-name "Nama Produk"  # tanpa riset
./login.sh --check     # cek sesi
./login.sh --credits    # cek kuota Flow
```

## 📁 Output per produk

```
products/<slug>/
├── research.json
├── images/            # gambar katalog
├── hd/                # hasil HD Nano Banana 2
├── storyboard.json
├── storyboard/       # scene01..03.png
├── clips/final_10s.mp4
└── final.mp4          # siap upload
```

## ⚠ Catatan jujur

- Google Flow tidak punya API publik; `gflow-cli` mengendalikan browser
  sesi milikmu (unofficial, alpha). Kuota Flow terpakai saat generate.
- API resmi TikTok Shop / Shopee butuh kredensial yang di-approve —
  riset memakai kurasi + Google Trends (best-effort), bukan data penjualan asli.
- Hasil AI tetap perlu dicek manual sebelum upload (anomali kadang lolos).

MIT — lihat `LICENSE`.
