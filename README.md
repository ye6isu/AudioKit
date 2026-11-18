# Audio Kit

A clean, minimalist desktop audio suite for tagging, hardware-compliant artwork encoding, and EBU R128 loudness normalization.

## Highlights
- **Native Desktop Application**: Built with PyQt6 and packaged as a standalone Windows executable (`AudioKit.exe`) — no scripts or terminal setup required.
- **Hardware-Compliant Cover Encoding**: Standardizes non-compliant and progressive artwork into Baseline RGB JPEG (Quality 95) for dedicated digital audio players.
- **EBU R128 Loudness Engine**: Measures integrated loudness (-18.00 LUFS target) and true sample peaks to write non-destructive ReplayGain tags.
- **Dual-Source Artwork Management**: Embed cover art by dropping images or extracting directly from existing music files.

## Architecture & Layout
```
AudioKit/
├── main.py                  # Desktop application entry point & layout
├── core/
│   └── engine.py            # Audio & tagging engine (Mutagen, Pillow, pyloudnorm)
├── gui/
│   ├── styles.py            # High-contrast minimalist dark stylesheet
│   ├── widgets.py           # Reusable drop zones and components
│   ├── tab_metadata.py      # Tag & Cover Editor tab
│   ├── tab_walkman.py       # Baseline JPEG Converter tab
│   ├── tab_replaygain.py    # ReplayGain Engine tab
│   └── tab_transfer.py      # Artwork Transfer tab
└── dist/
    └── AudioKit/
        └── AudioKit.exe     # Standalone portable Windows executable
```

## Running the Application

### 1. Standalone Binary (Recommended)
Run the compiled executable directly:
```
D:\Projects\Tools\AudioKit\dist\AudioKit\AudioKit.exe
```

### 2. From Source
```powershell
pip install PyQt6 mutagen pillow soundfile pyloudnorm numpy
python main.py
```

## Building Executable
```powershell
pyinstaller --noconsole --name "AudioKit" --exclude-module torch --exclude-module torchvision --exclude-module matplotlib --add-data "core;core" --add-data "gui;gui" main.py
```

## License
MIT License. Designed and developed by [Liam Andreu Gamboa (ye6isu)](https://github.com/ye6isu).
