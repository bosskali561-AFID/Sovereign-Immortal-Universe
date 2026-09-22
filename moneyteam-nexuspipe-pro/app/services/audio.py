"""Audio normalization: WAV-safe copy/normalization, non-WAV passthrough."""
from __future__ import annotations

import shutil
import wave
from pathlib import Path


def normalize_audio_dir(src: Path, out: Path) -> list[Path]:
    src = Path(src)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for wav_path in sorted(src.glob("*.wav")):
        with wave.open(str(wav_path), "rb") as w:
            params = w.getparams()
            frames = w.readframes(w.getnframes())
        target = out / wav_path.name
        with wave.open(str(target), "wb") as w:
            w.setparams(params)
            w.writeframes(frames)
        results.append(target)
    for p in sorted(src.iterdir()):
        if p.is_file() and p.suffix.lower() != ".wav":
            dst = out / p.name
            shutil.copy2(p, dst)
            results.append(dst)
    return results
