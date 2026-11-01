#!/usr/bin/env python3
"""Generate narration audio, timing data and SRT captions with the Piper voice.

One clip is synthesized per caption row, so every caption starts and ends
exactly where its speech does. Clips are trimmed, loudness-matched and joined
into one audio file per scene.

Usage (run with the Python that has piper-tts installed):
  python make_narration.py --model PATH/en-us-lessac-medium.onnx [--cut s6-11,s6-12]

Outputs:
  public/audio/<part>-<scene>.flac   one narration file per scene
  src/timing.json                    frame timings used by Remotion
  out/captions-part1.srt, out/captions-part2.srt
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import wave

import numpy as np
from piper import PiperVoice
from piper.config import SynthesisConfig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 30
OUT_SR = 24000

LEAD_IN = 0.6          # silence at the start of each scene
DEFAULT_GAP = 0.55     # pause between lines inside a scene
SCENE_TAIL = 1.0       # pause at the end of each scene (the "short pause between scenes")
SENTENCE_GAP = 0.3     # pause between sentences inside one caption row
TITLE_SECONDS = 3.0    # silent title card at the start of each part
TARGET_RMS_DB = -20.0  # per-line loudness match (voiced frames only)
# Final level for each scene file: +5 dB, with a gentle look-ahead peak limiter
# (latency-compensated, so timing does not move). Gives about -17 LUFS with peaks near -2 dBFS.
SCENE_FILTER = "volume=5dB,alimiter=limit=0.79:attack=5:release=60:latency=1:level=0"


def line_id(scene_id, idx):
    # Scene 4 in script.md starts its numbering at 0 (the "Last time" line).
    start = 0 if scene_id == "s4" else 1
    return f"{scene_id}-{idx + start}"


def synth(voice, text, length_scale):
    cfg = SynthesisConfig(length_scale=length_scale, normalize_audio=False)
    chunks = [c.audio_float_array for c in voice.synthesize(text, syn_config=cfg)]
    sr = voice.config.sample_rate
    gap = np.zeros(int(SENTENCE_GAP * sr), dtype=np.float32)
    parts = []
    for i, c in enumerate(chunks):
        c = trim(c, sr)
        if i:
            parts.append(gap)
        parts.append(c)
    return np.concatenate(parts), sr


def trim(a, sr, thresh_db=-45.0, pad=0.03):
    win = int(0.01 * sr)
    n = len(a) // win
    if n == 0:
        return a
    frames = a[: n * win].reshape(n, win)
    rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(rms / (np.max(rms) + 1e-12))
    voiced = np.where(db > thresh_db)[0]
    if len(voiced) == 0:
        return a
    s = max(0, voiced[0] * win - int(pad * sr))
    e = min(len(a), (voiced[-1] + 1) * win + int(pad * sr))
    return a[s:e]


def loudness_match(a, sr):
    win = int(0.02 * sr)
    n = len(a) // win
    frames = a[: n * win].reshape(n, win)
    rms = np.sqrt(np.mean(frames ** 2, axis=1) + 1e-12)
    voiced = rms[rms > np.max(rms) * 0.1]
    level = 20 * np.log10(np.sqrt(np.mean(voiced ** 2)) + 1e-12)
    gain = 10 ** ((TARGET_RMS_DB - level) / 20)
    out = a * gain
    peak = np.max(np.abs(out))
    if peak > 0.89:  # keep about 1 dB of headroom
        out = out * (0.89 / peak)
    return out


def write_wav(path, a, sr):
    pcm = (np.clip(a, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def srt_time(t):
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def srt_wrap(text, width=42):
    if len(text) <= width:
        return text
    words = text.split()
    best, best_diff = text, 10 ** 9
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        diff = abs(len(a) - len(b))
        if diff < best_diff:
            best, best_diff = a + "\n" + b, diff
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--length-scale", type=float, default=1.2)
    ap.add_argument("--cut", default="", help="comma-separated line ids to drop, e.g. s6-11,s6-12")
    args = ap.parse_args()
    cuts = {c.strip() for c in args.cut.split(",") if c.strip()}

    voice = PiperVoice.load(args.model)
    data = json.load(open(os.path.join(ROOT, "narration", "lines.json"), encoding="utf-8"))

    os.makedirs(os.path.join(ROOT, "public", "audio"), exist_ok=True)
    os.makedirs(os.path.join(ROOT, "out"), exist_ok=True)
    timing = {"fps": FPS, "voice": "Piper en-US lessac (medium)", "lengthScale": args.length_scale,
              "cuts": sorted(cuts), "parts": {}}
    report = []

    for part in data["parts"]:
        t_part = TITLE_SECONDS
        frame_cursor = int(round(TITLE_SECONDS * FPS))
        scenes_out, srt = [], []
        part_words, part_speech = 0, 0.0
        for scene in part["scenes"]:
            sr_out = OUT_SR
            pieces = [np.zeros(int(LEAD_IN * sr_out), dtype=np.float32)]
            t = LEAD_IN
            lines_out = []
            for idx, ln in enumerate(scene["lines"]):
                lid = line_id(scene["id"], idx)
                if lid in cuts:
                    continue
                hold = float(ln.get("hold", 0.0))
                if ln.get("silent"):
                    dur = hold
                    pieces.append(np.zeros(int(round(dur * sr_out)), dtype=np.float32))
                    lines_out.append({"id": lid, "text": "", "silent": True, "start": t, "end": t + dur})
                    t += dur
                    continue
                audio, sr = synth(voice, ln.get("tts", ln["text"]), args.length_scale)
                audio = loudness_match(audio, sr)
                # resample to OUT_SR with ffmpeg (soxr) via temp files
                with tempfile.TemporaryDirectory() as td:
                    src, dst = os.path.join(td, "a.wav"), os.path.join(td, "b.raw")
                    write_wav(src, audio, sr)
                    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af",
                                    "aresample=resampler=soxr", "-ar", str(sr_out), "-f", "f32le",
                                    "-ac", "1", dst], check=True)
                    audio = np.fromfile(dst, dtype=np.float32)
                dur = len(audio) / sr_out
                pieces.append(audio)
                lines_out.append({"id": lid, "text": ln["text"], "start": t, "end": t + dur,
                                  "cut": bool(ln.get("cut"))})
                part_words += len(ln["text"].split())
                part_speech += dur
                gap = float(ln.get("gapAfter", DEFAULT_GAP)) + hold
                pieces.append(np.zeros(int(round(gap * sr_out)), dtype=np.float32))
                t += dur + gap
            # replace the last gap with the scene tail
            last_gap = len(pieces[-1]) / sr_out
            pieces[-1] = np.zeros(int(round((last_gap - DEFAULT_GAP + SCENE_TAIL) * sr_out)), dtype=np.float32)
            scene_audio = np.concatenate(pieces)
            scene_dur = len(scene_audio) / sr_out
            dur_frames = int(np.ceil(scene_dur * FPS))
            # pad audio to whole frames so scenes line up exactly
            pad = dur_frames / FPS - scene_dur
            scene_audio = np.concatenate([scene_audio, np.zeros(int(round(pad * sr_out)), dtype=np.float32)])
            scene_start_s = frame_cursor / FPS

            name = f"{part['id']}-{scene['id']}"
            with tempfile.TemporaryDirectory() as td:
                wav = os.path.join(td, "s.wav")
                write_wav(wav, scene_audio, sr_out)
                subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", SCENE_FILTER, "-c:a", "flac",
                                os.path.join(ROOT, "public", "audio", name + ".flac")], check=True)

            for ln in lines_out:
                ln["startFrame"] = int(round(ln["start"] * FPS))
                ln["endFrame"] = int(round(ln["end"] * FPS))
                if not ln.get("silent"):
                    a = scene_start_s + ln["start"]
                    b = scene_start_s + ln["end"] + 0.2
                    srt.append((a, b, ln["text"]))
            scenes_out.append({"id": scene["id"], "title": scene["title"], "audio": f"audio/{name}.flac",
                               "startFrame": frame_cursor, "durationFrames": dur_frames,
                               "lines": lines_out})
            report.append(f"{name}: {scene_dur:6.1f}s  ({len(lines_out)} lines)")
            frame_cursor += dur_frames

        # make sure captions never overlap
        for i in range(len(srt) - 1):
            a, b, txt = srt[i]
            if b > srt[i + 1][0] - 0.04:
                srt[i] = (a, srt[i + 1][0] - 0.04, txt)
        with open(os.path.join(ROOT, "out", f"captions-{part['id']}.srt"), "w", encoding="utf-8") as f:
            for i, (a, b, txt) in enumerate(srt, 1):
                f.write(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{srt_wrap(txt)}\n\n")

        total = frame_cursor / FPS
        wpm = part_words / (part_speech / 60)
        timing["parts"][part["id"]] = {"title": part["title"], "titleFrames": int(round(TITLE_SECONDS * FPS)),
                                       "totalFrames": frame_cursor, "scenes": scenes_out}
        report.append(f"== {part['id']} total {int(total // 60)}:{total % 60:04.1f}  "
                      f"speech-only pace {wpm:.0f} wpm, overall {part_words / (total / 60):.0f} wpm")

    with open(os.path.join(ROOT, "src", "timing.json"), "w", encoding="utf-8") as f:
        json.dump(timing, f, indent=1, ensure_ascii=False)
    print("\n".join(report))


if __name__ == "__main__":
    sys.exit(main())
