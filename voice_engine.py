"""Voice engine: Text-to-Speech (edge-tts) + audio voice effects (ffmpeg)."""

import asyncio
import os
import tempfile
from pathlib import Path

import edge_tts

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Text-to-Speech with edge-tts (free, high quality, supports Burmese)
# ---------------------------------------------------------------------------

MYANMAR_VOICES = [
    ("my-MM-NilarNeural", "မြန်မာမိန်းမအသံ"),
    ("my-MM-ThihaNeural", "မြန်မာယောက်ကျားအသံ"),
]

ASIAN_VOICES = [
    ("zh-CN-XiaoxiaoNeural", "တရုပ်မိန်းမ (Xiaoxiao)"),
    ("zh-CN-YunjianNeural", "တရုပ်ယောက်ကျား (Yunjian)"),
    ("ja-JP-NanamiNeural", "ဂျပန်မိန်းမ (Nanami)"),
    ("ja-JP-KeitaNeural", "ဂျပန်ယောက်ကျား (Keita)"),
    ("ko-KR-SunHiNeural", "ကိုးရီးယားမိန်းမ (SunHi)"),
    ("ko-KR-HyunsuMultilingualNeural", "ကိုးရီးယားယောက်ကျား (Hyunsu)"),
    ("th-TH-PremwadeeNeural", "ထိုင်းမိန်းမ (Premwadee)"),
    ("th-TH-NiwatNeural", "ထိုင်းယောက်ကျား (Niwat)"),
]

ENGLISH_VOICES = [
    ("en-US-AriaNeural", "American မိန်းမ (Aria)"),
    ("en-US-GuyNeural", "American ယောက်ကျား (Guy)"),
    ("en-US-JennyNeural", "American မိန်းမ (Jenny)"),
    ("en-US-ChristopherNeural", "American ယောက်ကျား (Christopher)"),
]

ALL_VOICES = MYANMAR_VOICES + ASIAN_VOICES + ENGLISH_VOICES

SPEED_OPTIONS = {
    "အလွန်နှေး (-50%)": "-50%",
    "နှေး (-30%)": "-30%",
    "ပုံမှန်နှင့်အနည်းငယ်နှေး (-10%)": "-10%",
    "ပုံမှန် (0%)": "+0%",
    "ပုံမှန်နှင့်အနည်းငယ်မြန် (+10%)": "+10%",
    "မြန် (+30%)": "+30%",
    "အလွန်မြန် (+50%)": "+50%",
}

PITCH_OPTIONS = {
    "အလွန်နိမ့် (-20Hz)": "-20Hz",
    "နိမ့် (-10Hz)": "-10Hz",
    "ပုံမှန် (0Hz)": "+0Hz",
    "မြင့် (+10Hz)": "+10Hz",
    "အလွန်မြင့် (+20Hz)": "+20Hz",
}


def _normalize_pitch(pitch: str) -> str:
    """Convert a pitch string like '+0%' into edge-tts Hz format like '+0Hz'.

    edge-tts validates pitch with ^[+-]\\d+Hz$ and validates rate with
    ^[+-]\\d+%; it is easy to mix the two up, so normalize here to be safe.
    """
    pitch = pitch.strip()
    if pitch.endswith("Hz"):
        return pitch
    if pitch.endswith("%"):
        pitch = pitch[:-1]  # drop the percent sign
    if pitch.lstrip("+-").isdigit():
        return f"{pitch}Hz"
    return "+0Hz"


async def generate_tts(text: str, voice: str, speed: str,
                       rate_pct: str = "+0%", volume: str = "+0%") -> bytes:
    """Generate speech audio and return raw bytes."""
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=speed,
        pitch=_normalize_pitch(rate_pct),
        volume=volume,
    )
    chunks = bytearray()
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            chunks.extend(chunk["data"])
    return bytes(chunks)


def run_tts_to_file(text: str, voice: str, speed: str, rate_pct: str = "+0%",
                    volume: str = "+0%", suffix: str = "") -> Path:
    """Synchronous wrapper: write audio to an mp3 file, return its path."""
    data = asyncio.run(generate_tts_to_file_helper(text, voice, speed,
                                                   rate_pct, volume))
    path = OUTPUT_DIR / f"tts_{voice}_{suffix or 'custom'}.mp3"
    path.write_bytes(data)
    return path


async def generate_tts_to_file_helper(text: str, voice: str, speed: str,
                                      rate_pct: str, volume: str) -> bytes:
    return await generate_tts(text, voice, speed, rate_pct, volume)


# ---------------------------------------------------------------------------
# 2. Voice effects using ffmpeg (works on any uploaded audio file)
# ---------------------------------------------------------------------------

EFFECTS = {
    "ယောက်ကျားအသံ (နက်သောအသံ)": {
        "filters": ["asetrate=44100*0.85", "aresample=44100", "atempo=1.15"],
    },
    "ကလေးအသံ (Chipmunk)": {
        "filters": ["asetrate=44100*1.4", "aresample=44100", "atempo=0.8"],
    },
    "ကြည့်သောအသံ (High Pitch)": {
        "filters": ["asetrate=44100*1.15", "aresample=44100", "atempo=0.92"],
    },
    "ရိုဘတ်အသံ (Robot)": {
        "filters": [
            "asetrate=44100*0.7",
            "aresample=44100",
            "atremolo=10",
            "tremolo=f=30:d=0.8",
        ],
    },
    "ရေအောက်အသံ (Underwater)": {
        "filters": ["lowpass=f=700", "asetrate=44100*0.8", "aresample=44100"],
    },
    "ရေဒီယိုအသံ (Radio)": {
        "filters": ["highpass=f=300", "lowpass=f=3000", "asetrate=44100*0.9",
                    "aresample=44100"],
    },
    "ကြီးမားသောအသံ (Giant)": {
        "filters": ["asetrate=44100*0.65", "aresample=44100", "atempo=1.25"],
    },
    "ရုပ်ပြောင်းထွားချဲ့ (Echo)": {
        "filters": ["aecho=0.8:0.88:60:0.4", "asetrate=44100*0.95",
                    "aresample=44100"],
    },
}


def apply_effects(input_path: str, effect: str,
                  tempo: float = 1.0) -> Path:
    """Apply a named voice effect with ffmpeg; return output mp3 path."""
    if effect not in EFFECTS:
        raise ValueError(f"Unknown effect: {effect}")
    filters = list(EFFECTS[effect]["filters"])
    if abs(tempo - 1.0) > 0.01:
        filters.append(f"atempo={tempo:.2f}")
    filter_complex = ",".join(filters)
    out_path = OUTPUT_DIR / f"effect_{Path(input_path).stem}_{effect}.mp3"
    os.system(
        f'ffmpeg -y -loglevel error -i "{input_path}" '
        f'-af "{filter_complex}" -codec:a libmp3lame -q:a 4 "{out_path}"'
    )
    return out_path


def change_tempo(input_path: str, tempo: float) -> Path:
    """Change playback speed without pitch shift (tempo only)."""
    filter_complex = f"atempo={tempo:.2f}"
    out_path = OUTPUT_DIR / f"tempo_{tempo:.2f}_{Path(input_path).stem}.mp3"
    os.system(
        f'ffmpeg -y -loglevel error -i "{input_path}" '
        f'-af "{filter_complex}" -codec:a libmp3lame -q:a 4 "{out_path}"'
    )
    return out_path

