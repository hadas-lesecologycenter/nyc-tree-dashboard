# Handoff: Atom Models Explainer Videos

Read this file first, then `script.md`.

## Decisions already made (don't ask again)
- **Two videos, not one.** The full story runs about 7 min at 130 wpm, so it's split:
  - **Part 1** = Scenes 1–3 (Hook, Dalton, Thomson). About 3:00.
  - **Part 2** = Scenes 4–7 (Rutherford, Bohr, Quantum, Recap). About 4:25. This is close to the limit.
  - Each part must be **under 4½ min**. Every script line is kept. If Part 2 runs long after real timing, cut ✂ lines in the order listed in script.md under "Length".
  - Outputs: `atom-models-part1.mp4` and `atom-models-part2.mp4`, plus `captions-part1.srt` and `captions-part2.srt`.
- **Voice: ElevenLabs.** The user is adding `ELEVENLABS_API_KEY` and allowing `api.elevenlabs.io` in the environment's network settings.
  - Check that the key is set: `[ -n "$ELEVENLABS_API_KEY" ]`.
  - Check that the host is reachable: `curl -sS -o /dev/null -w '%{http_code}' https://api.elevenlabs.io/v1/models -H "xi-api-key: $ELEVENLABS_API_KEY"`.
  - If either check fails, tell the user. Fallback: Piper (below).
- **Script status:** `script.md` is a draft. The user has approved the two-part split. Confirm the wording itself before generating audio. The only new lines since the first draft are marked **(new)**.

## Environment findings (from the previous session)
- Node 22.23.4, npm 10.9.9, ffmpeg and ffprobe are installed. Remotion is not installed yet. registry.npmjs.org is reachable.
- Google Fonts (fonts.googleapis.com) is reachable. cdn.jsdelivr.net and huggingface.co are **blocked**. To get Atkinson Hyperlegible, use the `@remotion/google-fonts` package or download it from fonts.googleapis.com.
- Piper fallback, tested and working:
  - `python3 -m venv piper-venv && piper-venv/bin/pip install piper-tts`
  - Voice download from GitHub (HuggingFace is blocked): `https://github.com/rhasspy/piper/releases/download/v0.0.2/voice-en-us-lessac-medium.tar.gz`
  - The voice's natural rate is about 160 wpm. Use `--length-scale` of about 1.2 to get about 130 wpm.
  - Piper gives no timestamps. Synthesize one clip per caption sentence and concatenate them, so caption timing is exact.

## Build plan
1. Confirm the script, then generate one audio file per scene per part.
   - Use the ElevenLabs endpoint that returns character timestamps (check the current docs).
   - List the available voices and pick a warm, clear one.
   - Write the captions as SRT files. Each caption is one script row and at most 2 lines.
2. Build the Remotion project (React + TypeScript) in this folder. Use 1920×1080, 30 fps, H.264 + AAC.
   - Render a low-res preview and take screenshots from the start, middle and end of every scene. Fix problems, then render the finals.
3. Run the final check from the brief below and report the file paths.

---

## Original brief from the user (verbatim)

Make a short animated explainer video (about 4 minutes, no more than 4½) about the models of the atom. It's for a 10th grader with learning disabilities who finds reading hard. It must be engaging, very simple, and scientifically accurate. It goes with a high school chemistry unit, so use the class's names for the models:
Solid Sphere (Dalton, 1803), Plum Pudding (Thomson, 1904), Nuclear Model (Rutherford, 1911), Planetary Model (Bohr, 1913), Quantum Model (Schrödinger, 1926).

The big idea the student should leave with: each model made a prediction, an experiment tested it, the result didn't fit, and scientists updated the model. Science changes its mind when the evidence says so.

### Rules for this student (apply everywhere)
- Narration does the teaching. On-screen text is short labels only (about 6 words max), never paragraphs.
- Short sentences (12 words or fewer) and everyday words. Define every science word the first time it appears, with a picture (for example: "nucleus: the tiny center of the atom").
- Slow, calm pace: about 130 words per minute, with a short pause between scenes.
- Burned-in captions synced to the voice: large (at least 48 px at 1080p), max 2 lines, high contrast on a solid backing box, at the bottom of the screen.
- Font: Atkinson Hyperlegible or Lexend (Google Fonts).
- One idea on screen at a time. Never rely on color alone: also label with +, − or words.
- Nothing flashes more than 3 times per second. No background music. A few soft sound effects are OK.

### Tech
- Build it with Remotion (React + TypeScript) in a new folder called atom-models-video. Check what's installed first and install what's missing.
- Draw every visual as original shapes/SVG in code. Use no images, photos or portraits from the web. Show each scientist as a name card (name, country, year) with a simple generic silhouette.
- Output: 1920×1080, 30 fps, MP4 (H.264 + AAC).
- Narration: use the ElevenLabs API if the ELEVENLABS_API_KEY environment variable is set.
  - Check the current ElevenLabs API docs for the right endpoint and model.
  - List the available voices and pick a warm, clear, friendly one.
  - Use the endpoint that returns timing data (character or word timestamps) so captions and animations line up exactly with the voice.
  - Make one audio file per scene.
- If there's no key, ask me once whether I want to add one. If not, use a free local neural voice such as Piper if it installs cleanly. Use the computer's built-in voice only as a last resort.
- Don't ask me questions you can answer yourself. The only stops are the API key question and the script approval below.

### Work in this order
1. Write the narration script to script.md, scene by scene, with timing estimates and a short note of what's on screen. Show it to me and WAIT for my OK.
2. Generate the narration audio. Also save the captions as captions.srt.
3. Build the animation. Render a low-resolution preview first and take screenshots from every scene. Fix problems, then render the final video as atom-models.mp4.
4. Run the final check (bottom), then tell me where the files are.

### Visual language (keep it consistent)
- Electron: small blue circle with "−". Positive charge / proton: red with "+". Neutron: gray, no sign. Alpha particle: yellow with "+". Gold foil: gold.
- The models should look like the class drawings:
  - Solid Sphere: one solid ball.
  - Plum Pudding: a big ball of spread-out positive charge with electrons stuck in it.
  - Nuclear: a tiny + nucleus with electrons moving on crossing paths and lots of empty space.
  - Planetary: a nucleus with electrons on circular rings.
  - Quantum: a fuzzy dot cloud around the nucleus.
- A timeline bar at the TOP of the screen (1803 → 1926) lights up the current model, starting at Dalton.
- Every model change follows the same pattern so it's predictable: THE MODEL → WHAT IT PREDICTS → THE EXPERIMENT → WHAT REALLY HAPPENED → NEW MODEL. Show "Prediction" and "Result" side by side so the mismatch is obvious.
- When a model is replaced, stamp it "UPDATED" (not "WRONG") and slide it onto the timeline.
- Playful but calm motion: things pop in with a gentle bounce, beams glow, particles leave trails.

### The story, scene by scene
(script.md now holds the full scene-by-scene content. It covers every fact from the original brief: the pencil and graphite hook; atomos; Democritus and Leucippus versus Aristotle; Lavoisier's and Proust's laws; Dalton's three ideas; the cathode ray tube and its three discoveries; electrons over 1,000 times lighter than hydrogen; Plum Pudding as a blueberry muffin; the gold foil experiment with Geiger and Marsden, the flash screen, the 1-in-8,000 bounce-back with slow-motion replay, the 15-inch shell quote, and the baseball/5-mile scale; the 1932 Chadwick neutron side note; hydrogen lines at 656/486/434/410 nm; flame tests (sodium yellow-orange, lithium red, potassium violet, barium green); the staircase analogy; animations of n=3→2 (red) and n=5→2 (violet 434 nm); de Broglie 1924; Schrödinger 1926 orbitals; Heisenberg 1927; the 1,000-snapshot cloud; the G. P. Thomson / J. J. Thomson Nobel fun fact; the recap with evidence arrows; and the last line "Each experiment didn't throw science away. It made our picture of the atom better.")

### Accuracy guardrails
- Thomson's "pudding" is spread-out positive charge, NOT protons.
- Rutherford's Nuclear Model has no fixed rings or orbits. Those are Bohr's.
- The cathode ray goes from cathode (−) to anode (+). Alpha particles are positive.
- The gold foil experiment did not discover the proton or the neutron.
- Orbitals are regions where an electron is likely to be, not paths.
- Keep the dates exactly as listed here. If you're unsure of any other fact, leave it out rather than guess.

### Final check before you hand it over
- Look at screenshots from the start, middle and end of every scene. Check that text is readable, nothing is cut off, and captions never cover the key visual.
- Captions match the voice to within about 0.2 seconds.
- Every name is spelled right: Democritus, Leucippus, Aristotle, Antoine Lavoisier, Joseph Proust, John Dalton, J. J. Thomson, Ernest Rutherford, Hans Geiger, Ernest Marsden, James Chadwick, Niels Bohr, Louis de Broglie, Erwin Schrödinger, Werner Heisenberg, G. P. Thomson.
- Total length is under 4½ minutes, and the audio volume is even with no distortion.
- Re-read script.md against the accuracy guardrails one last time.
