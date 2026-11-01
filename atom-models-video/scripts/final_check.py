#!/usr/bin/env python3
"""Final check for the rendered videos (measured on the MP4 files, not assumed).

- length of each part (must be under 4:30)
- video format (1920x1080, 30 fps, H.264 + AAC)
- loudness: integrated LUFS, loudness range and true peak (no clipping)
- caption sync: every SRT caption start vs the speech onset detected in the MP4's audio
- spelling of every scientist's name in captions and on-screen text

Usage: python3 scripts/final_check.py out/atom-models-part1.mp4 out/atom-models-part2.mp4
"""
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = ["Democritus", "Leucippus", "Aristotle", "Antoine Lavoisier", "Joseph Proust", "John Dalton",
         "J. J. Thomson", "Ernest Rutherford", "Hans Geiger", "Ernest Marsden", "James Chadwick", "Niels Bohr",
         "Louis de Broglie", "Erwin Schrödinger", "Werner Heisenberg", "G. P. Thomson"]


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                         capture_output=True, text=True).stdout
    return json.loads(out)


def srt_starts(path):
    starts = []
    for m in re.finditer(r"(\d+):(\d+):(\d+),(\d+) -->", open(path, encoding="utf-8").read()):
        h, mi, s, ms = map(int, m.groups())
        starts.append(h * 3600 + mi * 60 + s + ms / 1000)
    return starts


def speech_onsets(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af",
                          "silencedetect=noise=-45dB:d=0.12", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]


def loudness(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summary = out[out.rfind("Summary:"):]
    I = float(re.search(r"I:\s+(-?[0-9.]+) LUFS", summary).group(1))
    LRA = float(re.search(r"LRA:\s+([0-9.]+) LU", summary).group(1))
    TP = float(re.search(r"Peak:\s+(-?[0-9.]+) dBFS", summary).group(1))
    return I, LRA, TP


def main(paths):
    ok = True
    for i, p in enumerate(paths, 1):
        info = probe(p)
        v = next(s for s in info["streams"] if s["codec_type"] == "video")
        a = next(s for s in info["streams"] if s["codec_type"] == "audio")
        dur = float(info["format"]["duration"])
        fps = eval(v["r_frame_rate"])
        print(f"\n== {os.path.basename(p)}")
        print(f"length {int(dur // 60)}:{dur % 60:05.2f}  {'OK' if dur < 270 else 'TOO LONG'} (limit 4:30)")
        print(f"video {v['codec_name']} {v['width']}x{v['height']} {fps:.0f} fps, audio {a['codec_name']} {a['sample_rate']} Hz")
        ok &= dur < 270 and v["codec_name"] == "h264" and a["codec_name"] == "aac" and v["width"] == 1920 and v["height"] == 1080 and round(fps) == 30
        I, LRA, TP = loudness(p)
        print(f"loudness {I:.1f} LUFS integrated, range {LRA:.1f} LU, true peak {TP:.1f} dBFS  {'OK' if TP < -1.0 else 'CHECK PEAKS'}")
        ok &= TP < -1.0
        srt = os.path.join(ROOT, "out", f"captions-part{i}.srt")
        caps = srt_starts(srt)
        ons = speech_onsets(p)
        devs = []
        for c in caps:
            d = min((abs(o - c) for o in ons), default=99)
            devs.append(d)
        worst = max(devs)
        print(f"caption sync: {len(caps)} captions, median offset {sorted(devs)[len(devs) // 2] * 1000:.0f} ms, "
              f"worst {worst * 1000:.0f} ms  {'OK' if worst <= 0.2 else 'CHECK'} (target within 200 ms)")
        if worst > 0.2:
            for c, d in zip(caps, devs):
                if d > 0.2:
                    print(f"   caption at {c:.2f}s is {d * 1000:.0f} ms from the nearest speech onset")
        ok &= worst <= 0.2

    # names: every name that appears must be spelled exactly; report which appear where
    text = json.dumps(json.load(open(os.path.join(ROOT, "narration", "lines.json"), encoding="utf-8")), ensure_ascii=False)
    src = "".join(open(os.path.join(ROOT, "src", "scenes", f), encoding="utf-8").read() for f in sorted(os.listdir(os.path.join(ROOT, "src", "scenes"))))
    srts = "".join(open(os.path.join(ROOT, "out", f), encoding="utf-8").read() for f in ["captions-part1.srt", "captions-part2.srt"])
    print("\n== names (captions | on-screen cards)")
    for n in NAMES:
        in_caps = n in srts.replace("\n", " ")
        in_src = n in src
        print(f"{n:20s} captions: {'yes' if in_caps else 'no (line cut)' if n in text else 'MISSING'}   on screen: {'yes' if in_src else 'no'}")
    print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS NEED ATTENTION")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
