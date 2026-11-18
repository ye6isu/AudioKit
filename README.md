# Audio Kit

<p align="center">
  <b>A minimalist, utility-first desktop audio suite for tagging, artwork compliance, and loudness normalization.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/GUI-PyQt6-brightgreen?style=flat-square" alt="PyQt6">
  <img src="https://img.shields.io/badge/Standard-EBU%20R128%20%2F%20ReplayGain%202.0-orange?style=flat-square" alt="ReplayGain">
  <img src="https://img.shields.io/badge/Target-Walkman%20%26%20DAP%20Ready-purple?style=flat-square" alt="Walkman Ready">
</p>

---

## Overview

Modern digital music files often suffer from inconsistent volumes, broken metadata, and incompatible embedded cover artwork. Older or specialized hardware audio players—such as **Sony Walkmans**, classic DAPs, and automotive head units—regularly fail to render progressive JPEG artwork, CMYK color profiles, or oversized embedded images.

**Audio Kit** is a unified desktop utility that solves these problems with a focus on simplicity and workflow separation:
- **No bloat**: Each function is clearly separated into its own purpose-built view.
- **Fast drag-and-drop**: Drop songs, albums, or entire music libraries directly into the application.
- **Hardware compliant**: Guarantees baseline JPEG cover art compatibility for legacy and dedicated audio players.

---

## Features

### 🏷️ 1. Metadata & Artwork Inspector / Editor
- View and edit standard tags: **Title, Artist, Album, Album Artist, Track #, Disc #, Year, Genre**.
- Supports FLAC (Vorbis comments) and MP3 (ID3v2).
- Drop image files directly onto the artwork card to replace and embed cover art.
- Live compatibility badge indicating whether current artwork meets player standards.

### ✨ 2. Walkman & DAP Cover Fixer
- Deep inspection of embedded artwork structures.
- Detects and fixes progressive JPEGs, non-RGB modes, and non-standard image encodings.
- Batch re-encodes artwork to **Baseline JPEG (Quality 95, RGB)** with a single click.
- Deduplicates corrupted multi-valued artist and genre tags.

### 📊 3. ReplayGain 2.0 Loudness Normalizer
- Accurate **EBU R128** integrated loudness calculation via `pyloudnorm` and true sample peak detection via `soundfile`.
- Standardized target loudness of **-18.00 LUFS**.
- Writes non-destructive `REPLAYGAIN_TRACK_GAIN`, `REPLAYGAIN_TRACK_PEAK`, `REPLAYGAIN_ALBUM_GAIN`, and `REPLAYGAIN_ALBUM_PEAK` tags.

### 🔄 4. Artwork Cloner & Transfer
- Separate **Source** and **Target** drop zones.
- Inherit cover art from an existing track (FLAC/MP3) or image file.
- Batch-applies the inherited cover to target tracks or folders in Walkman-compliant format.

---

## Architecture & Separation of Concerns

```
AudioKit/
├── AudioKit.bat             # 1-Click Windows Launcher
├── main.py                  # Application entry point & sidebar layout
├── core/
│   └── engine.py            # Headless processing engine (Pillow, Mutagen, pyloudnorm)
├── gui/
│   ├── styles.py            # Minimalist dark theme stylesheet
│   ├── widgets.py           # Reusable Drag & Drop zones and custom components
│   ├── tab_metadata.py      # Tag & Cover Editor tab
│   ├── tab_walkman.py       # Baseline JPEG standardizer tab
│   ├── tab_replaygain.py    # EBU R128 loudness tagger tab
│   └── tab_transfer.py      # Dual-zone artwork cloner tab
└── assets/                  # Icons and branding assets
```

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ye6isu/AudioKit.git
   cd AudioKit
   ```

2. **Install dependencies**:
   ```bash
   pip install PyQt6 mutagen pillow soundfile pyloudnorm numpy
   ```

3. **Run Audio Kit**:
   ```bash
   python main.py
   ```
   *Or simply double-click `AudioKit.bat` on Windows.*

---

## Building Standalone Executable (.exe)

To bundle Audio Kit as a standalone Windows application with PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconsole --name "AudioKit" --add-data "core;core" --add-data "gui;gui" main.py
```
The compiled executable will be placed in the `dist/AudioKit` directory.

---

## License

MIT License. Designed and developed by [Liam Andreu Gamboa (ye6isu)](https://github.com/ye6isu).
