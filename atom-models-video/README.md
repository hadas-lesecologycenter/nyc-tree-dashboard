# Models of the Atom: explainer videos

Two short animated explainers for a 10th-grade chemistry unit, built with Remotion (React + TypeScript).
The script is in `script.md`, and `HANDOFF.md` holds the original brief.

| Output | File |
|---|---|
| Part 1: From Solid Balls to Plum Pudding (Scenes 1–3) | `out/atom-models-part1.mp4` |
| Part 2: From Gold Foil to the Quantum Model (Scenes 4–7) | `out/atom-models-part2.mp4` |
| Captions (also burned into the videos) | `out/captions-part1.srt`, `out/captions-part2.srt` |

## How it is made

- **Narration:** Piper neural TTS, voice `en_US-lessac-medium`, run locally. ElevenLabs was not available in the build session: there was no API key, and the network policy blocked `api.elevenlabs.io`.
  - One clip is made per caption row, so captions start exactly when their sentence starts.
  - Names and years are spelled phonetically for the voice only (the `tts` field in `narration/lines.json`). The captions keep the real spelling.
  - Clips are trimmed, loudness-matched, and joined into one audio file per scene (`public/audio/*.flac`).
- **Timing:** `scripts/make_narration.py` writes `src/timing.json`. Every animation cue is keyed to a narration line ID (for example `s4-13`), so visuals follow the voice.
- **Visuals:** every shape is drawn in code (SVG). Scientists appear as name cards with a generic silhouette. No images are downloaded.
- **Font:** Atkinson Hyperlegible (SIL Open Font License), bundled in `public/fonts`.
- **Sound effects:** two soft tones (a "pop" and a "stamp"), generated with ffmpeg. There is no music.

## Rebuild

```bash
npm install
# narration (needs piper-tts and the en_US-lessac-medium voice)
python scripts/make_narration.py --model PATH/en-us-lessac-medium.onnx --length-scale 1.45 --cut s6-11,s6-12,s6-13
# stills: start / middle / end of each scene, or one per narration line with --lines
REMOTION_BROWSER=/path/to/chrome-headless-shell node scripts/stills.mjs Part1
# final renders
REMOTION_BROWSER=/path/to/chrome-headless-shell npx remotion render Part1 out/atom-models-part1.mp4
REMOTION_BROWSER=/path/to/chrome-headless-shell npx remotion render Part2 out/atom-models-part2.mp4
python3 scripts/final_check.py out/atom-models-part1.mp4 out/atom-models-part2.mp4
```

Run `make_narration.py` with the Python that has `piper-tts` installed.

**Cuts:** Part 2 ran over 4½ minutes with every line in. Following the cut order in `script.md`, only the first item was cut: Scene 6 #11–13, the G. P. Thomson fun fact. To restore those lines, drop `--cut`, re-run the narration, and check that Part 2 stays under 4:30. Their animations are still in `Scene6.tsx`.
