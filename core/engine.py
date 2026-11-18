"""
Audio Kit - Audio & Metadata Processing Engine
Unified core operations:
- Metadata tag read/write and deduplication
- Baseline JPEG cover art standardization and transfer
- ReplayGain / EBU R128 loudness analysis (-18 LUFS)
- High-fidelity Audio Trimming (sample-accurate start/end slicing)
- Audio Format Conversion (FLAC, MP3, WAV, OGG, AIFF) with metadata preservation
"""

import os
import io
import shutil
from pathlib import Path
from PIL import Image
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
import mutagen
from mutagen.flac import FLAC, Picture
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TXXX, TIT2, TPE1, TALB, TDRC, TCON, TRCK, TPOS, TPE2, ID3NoHeaderError

SUPPORTED_AUDIO_EXTENSIONS = {'.flac', '.mp3', '.m4a', '.mp4', '.ogg', '.opus', '.wav', '.aiff'}
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
DEFAULT_TARGET_LUFS = -18.0

def scan_audio_files(paths, recursive=True):
    matched = []
    for p in paths:
        p_obj = Path(p)
        if p_obj.is_file():
            if p_obj.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                matched.append(str(p_obj.resolve()))
        elif p_obj.is_dir():
            pattern = "**/*" if recursive else "*"
            for item in p_obj.glob(pattern):
                if item.is_file() and item.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS:
                    matched.append(str(item.resolve()))
    return sorted(list(dict.fromkeys(matched)))

def convert_to_baseline_jpeg(img_bytes, max_dim=None, quality=95):
    img = Image.open(io.BytesIO(img_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    if max_dim:
        w, h = img.size
        if max(w, h) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
    out = io.BytesIO()
    img.save(out, format='JPEG', quality=quality, progressive=False)
    return out.getvalue(), img.width, img.height

def inspect_cover_art(img_bytes):
    try:
        img = Image.open(io.BytesIO(img_bytes))
        is_prog = bool(img.info.get('progressive', False))
        fmt = (img.format or "").upper()
        mode = img.mode
        needs_fix = is_prog or (mode not in ('RGB', 'L')) or (fmt != 'JPEG')
        return {
            'needs_fix': needs_fix,
            'is_progressive': is_prog,
            'format': fmt,
            'mode': mode,
            'size': img.size,
            'error': None
        }
    except Exception as e:
        return {
            'needs_fix': True,
            'is_progressive': False,
            'format': 'UNKNOWN',
            'mode': 'UNKNOWN',
            'size': (0, 0),
            'error': str(e)
        }

def extract_artwork(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in SUPPORTED_IMAGE_EXTENSIONS:
        with open(file_path, 'rb') as f:
            data = f.read()
        mime = 'image/jpeg' if ext in ('.jpg', '.jpeg') else f'image/{ext[1:]}'
        return data, mime

    try:
        if ext == '.flac':
            audio = FLAC(file_path)
            if audio.pictures:
                front = [p for p in audio.pictures if p.type == 3]
                pic = front[0] if front else audio.pictures[0]
                return pic.data, pic.mime
        elif ext == '.mp3':
            audio = MP3(file_path)
            if audio.tags:
                apics = [v for k, v in audio.tags.items() if k.startswith('APIC')]
                if apics:
                    front = [p for p in apics if getattr(p, 'type', None) == 3]
                    pic = front[0] if front else apics[0]
                    return pic.data, pic.mime
        else:
            audio = mutagen.File(file_path)
            if audio is not None:
                if hasattr(audio, 'pictures') and audio.pictures:
                    return audio.pictures[0].data, audio.pictures[0].mime
                if hasattr(audio, 'tags') and audio.tags:
                    for k, v in audio.tags.items():
                        if k.startswith('APIC'):
                            return v.data, getattr(v, 'mime', 'image/jpeg')
    except Exception:
        pass
    return None, None

def set_artwork(file_path, img_bytes, standardize_baseline=True):
    ext = os.path.splitext(file_path)[1].lower()
    if standardize_baseline:
        cover_data, w, h = convert_to_baseline_jpeg(img_bytes)
        mime = 'image/jpeg'
    else:
        cover_data = img_bytes
        try:
            im = Image.open(io.BytesIO(img_bytes))
            w, h = im.size
            mime = 'image/jpeg' if im.format == 'JPEG' else 'image/png'
        except Exception:
            w, h = 500, 500
            mime = 'image/jpeg'

    if ext == '.flac':
        audio = FLAC(file_path)
        p = Picture()
        p.type = 3
        p.mime = mime
        p.desc = 'Cover'
        p.width = w
        p.height = h
        p.depth = 24
        p.data = cover_data
        audio.clear_pictures()
        audio.add_picture(p)
        audio.save()
        return True

    elif ext == '.mp3':
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()
        apic_keys = [k for k in audio.keys() if k.startswith('APIC')]
        for k in apic_keys:
            del audio[k]
        audio.add(APIC(
            encoding=3,
            mime=mime,
            type=3,
            desc='Cover',
            data=cover_data
        ))
        audio.save(file_path)
        return True

    return False

def remove_artwork(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.flac':
        audio = FLAC(file_path)
        if audio.pictures:
            audio.clear_pictures()
            audio.save()
            return True
    elif ext == '.mp3':
        try:
            audio = ID3(file_path)
            apics = [k for k in audio.keys() if k.startswith('APIC')]
            if apics:
                for k in apics:
                    del audio[k]
                audio.save(file_path)
                return True
        except Exception:
            pass
    return False

def deduplicate_tags(audio_tags):
    if not audio_tags:
        return False
    changed = False
    for key in list(audio_tags.keys()):
        val = audio_tags[key]
        if isinstance(val, list) and len(val) > 1:
            seen = set()
            deduped = []
            for item in val:
                normalized = item.strip().lower() if isinstance(item, str) else item
                if normalized not in seen:
                    seen.add(normalized)
                    deduped.append(item)
            if len(deduped) != len(val):
                audio_tags[key] = deduped
                changed = True
    return changed

def read_audio_metadata(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    meta = {
        'filepath': file_path,
        'filename': os.path.basename(file_path),
        'title': '',
        'artist': '',
        'album': '',
        'albumartist': '',
        'track': '',
        'disc': '',
        'year': '',
        'genre': '',
        'duration_sec': 0.0,
        'has_art': False,
        'art_info': None,
        'art_bytes': None
    }

    raw_art, mime = extract_artwork(file_path)
    if raw_art:
        meta['has_art'] = True
        meta['art_info'] = inspect_cover_art(raw_art)
        meta['art_bytes'] = raw_art

    if ext == '.flac':
        try:
            audio = FLAC(file_path)
            meta['duration_sec'] = float(getattr(audio.info, 'length', 0.0))
            def get_f(key):
                v = audio.get(key, [])
                return ', '.join(v) if isinstance(v, list) else str(v)
            meta['title'] = get_f('title')
            meta['artist'] = get_f('artist')
            meta['album'] = get_f('album')
            meta['albumartist'] = get_f('albumartist') or get_f('album_artist')
            meta['track'] = get_f('tracknumber')
            meta['disc'] = get_f('discnumber')
            meta['year'] = get_f('date') or get_f('year')
            meta['genre'] = get_f('genre')
        except Exception:
            pass

    elif ext == '.mp3':
        try:
            audio = MP3(file_path)
            meta['duration_sec'] = float(getattr(audio.info, 'length', 0.0))
            if audio.tags:
                tags = audio.tags
                def get_id3(frame):
                    f = tags.get(frame)
                    if f and hasattr(f, 'text') and f.text:
                        return ', '.join(str(t) for t in f.text)
                    return ''
                meta['title'] = get_id3('TIT2')
                meta['artist'] = get_id3('TPE1')
                meta['album'] = get_id3('TALB')
                meta['albumartist'] = get_id3('TPE2')
                meta['track'] = get_id3('TRCK')
                meta['disc'] = get_id3('TPOS')
                meta['year'] = get_id3('TDRC')
                meta['genre'] = get_id3('TCON')
        except Exception:
            pass

    # Fallback to soundfile duration
    if meta['duration_sec'] == 0.0:
        try:
            info = sf.info(file_path)
            meta['duration_sec'] = float(info.duration)
        except Exception:
            pass

    return meta

def save_audio_metadata(file_path, updates):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.flac':
        audio = FLAC(file_path)
        if 'title' in updates: audio['title'] = [updates['title']] if updates['title'] else []
        if 'artist' in updates: audio['artist'] = [updates['artist']] if updates['artist'] else []
        if 'album' in updates: audio['album'] = [updates['album']] if updates['album'] else []
        if 'albumartist' in updates:
            audio['albumartist'] = [updates['albumartist']] if updates['albumartist'] else []
        if 'track' in updates: audio['tracknumber'] = [updates['track']] if updates['track'] else []
        if 'disc' in updates: audio['discnumber'] = [updates['disc']] if updates['disc'] else []
        if 'year' in updates: audio['date'] = [updates['year']] if updates['year'] else []
        if 'genre' in updates: audio['genre'] = [updates['genre']] if updates['genre'] else []
        audio.save()
        return True

    elif ext == '.mp3':
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()
        if 'title' in updates:
            audio.setall('TIT2', [TIT2(encoding=3, text=[updates['title']])]) if updates['title'] else audio.delall('TIT2')
        if 'artist' in updates:
            audio.setall('TPE1', [TPE1(encoding=3, text=[updates['artist']])]) if updates['artist'] else audio.delall('TPE1')
        if 'album' in updates:
            audio.setall('TALB', [TALB(encoding=3, text=[updates['album']])]) if updates['album'] else audio.delall('TALB')
        if 'albumartist' in updates:
            audio.setall('TPE2', [TPE2(encoding=3, text=[updates['albumartist']])]) if updates['albumartist'] else audio.delall('TPE2')
        if 'track' in updates:
            audio.setall('TRCK', [TRCK(encoding=3, text=[updates['track']])]) if updates['track'] else audio.delall('TRCK')
        if 'disc' in updates:
            audio.setall('TPOS', [TPOS(encoding=3, text=[updates['disc']])]) if updates['disc'] else audio.delall('TPOS')
        if 'year' in updates:
            audio.setall('TDRC', [TDRC(encoding=3, text=[updates['year']])]) if updates['year'] else audio.delall('TDRC')
        if 'genre' in updates:
            audio.setall('TCON', [TCON(encoding=3, text=[updates['genre']])]) if updates['genre'] else audio.delall('TCON')
        audio.save(file_path)
        return True

    return False

def calculate_loudness_and_peak(file_path, target_lufs=DEFAULT_TARGET_LUFS):
    data, rate = sf.read(file_path, dtype='float32')
    meter = pyln.Meter(rate)
    loudness = meter.integrated_loudness(data)
    peak = float(np.max(np.abs(data)))
    gain_db = target_lufs - loudness
    return gain_db, peak, loudness

def apply_replaygain_tags(file_path, track_gain, track_peak, album_gain=None, album_peak=None):
    ext = os.path.splitext(file_path)[1].lower()
    track_gain_str = f"{track_gain:+.2f} dB"
    track_peak_str = f"{track_peak:.6f}"
    album_gain_str = f"{album_gain:+.2f} dB" if album_gain is not None else None
    album_peak_str = f"{album_peak:.6f}" if album_peak is not None else None

    if ext == '.flac':
        audio = FLAC(file_path)
        audio['replaygain_track_gain'] = [track_gain_str]
        audio['replaygain_track_peak'] = [track_peak_str]
        if album_gain_str:
            audio['replaygain_album_gain'] = [album_gain_str]
        if album_peak_str:
            audio['replaygain_album_peak'] = [album_peak_str]
        audio.save()
        return True

    elif ext == '.mp3':
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()
        audio.setall('TXXX:replaygain_track_gain', [TXXX(encoding=3, desc='replaygain_track_gain', text=[track_gain_str])])
        audio.setall('TXXX:replaygain_track_peak', [TXXX(encoding=3, desc='replaygain_track_peak', text=[track_peak_str])])
        if album_gain_str:
            audio.setall('TXXX:replaygain_album_gain', [TXXX(encoding=3, desc='replaygain_album_gain', text=[album_gain_str])])
        if album_peak_str:
            audio.setall('TXXX:replaygain_album_peak', [TXXX(encoding=3, desc='replaygain_album_peak', text=[album_peak_str])])
        audio.save(file_path)
        return True

    return False

# --- Audio Trimming & Format Conversion ---

def trim_audio_file(source_path, dest_path, start_sec, end_sec):
    """
    Sample-accurate audio trimming.
    Reads audio samples between start_sec and end_sec, writes to dest_path,
    and preserves all metadata and embedded cover artwork.
    """
    info = sf.info(source_path)
    sr = info.samplerate
    start_frame = max(0, int(start_sec * sr))
    end_frame = min(info.frames, int(end_sec * sr))

    if end_frame <= start_frame:
        raise ValueError("End time must be strictly greater than start time.")

    data, rate = sf.read(source_path, start=start_frame, stop=end_frame, dtype='float32')
    
    # Save trimmed audio
    target_ext = os.path.splitext(dest_path)[1].lower()
    fmt_map = {'.flac': 'FLAC', '.wav': 'WAV', '.mp3': 'MP3', '.ogg': 'OGG', '.aiff': 'AIFF'}
    sf_fmt = fmt_map.get(target_ext, 'FLAC')
    sf.write(dest_path, data, rate, format=sf_fmt)

    # Transfer metadata tags & artwork if FLAC or MP3
    try:
        orig_meta = read_audio_metadata(source_path)
        save_audio_metadata(dest_path, orig_meta)
        if orig_meta.get('has_art') and orig_meta.get('art_bytes'):
            set_artwork(dest_path, orig_meta['art_bytes'], standardize_baseline=True)
    except Exception:
        pass

    return True

def convert_audio_format(source_path, dest_format_ext, output_dir=None):
    """
    Converts audio track to target format (.flac, .mp3, .wav, .ogg).
    Preserves sample rate, channels, tags, and cover artwork.
    """
    dest_format_ext = dest_format_ext.lower()
    if not dest_format_ext.startswith('.'):
        dest_format_ext = '.' + dest_format_ext

    base_name = os.path.splitext(os.path.basename(source_path))[0]
    out_dir = output_dir or os.path.dirname(source_path)
    out_path = os.path.join(out_dir, f"{base_name}{dest_format_ext}")

    data, rate = sf.read(source_path, dtype='float32')
    fmt_map = {'.flac': 'FLAC', '.wav': 'WAV', '.mp3': 'MP3', '.ogg': 'OGG', '.aiff': 'AIFF'}
    sf_fmt = fmt_map.get(dest_format_ext, 'FLAC')
    sf.write(out_path, data, rate, format=sf_fmt)

    # Migrate metadata & cover
    try:
        orig_meta = read_audio_metadata(source_path)
        save_audio_metadata(out_path, orig_meta)
        if orig_meta.get('has_art') and orig_meta.get('art_bytes'):
            set_artwork(out_path, orig_meta['art_bytes'], standardize_baseline=True)
    except Exception:
        pass

    return out_path
