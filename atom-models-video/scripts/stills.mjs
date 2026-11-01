// Renders screenshots from the start, middle and end of every scene (or of chosen shots),
// then tiles them into contact sheets. Usage:
//   node scripts/stills.mjs Part1 [s1,s2] [--lines]   (--lines: one still per narration line instead)
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const [compId = "Part1", sceneFilter = "", flag = ""] = process.argv.slice(2);
const root = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const timing = JSON.parse(fs.readFileSync(path.join(root, "src/timing.json"), "utf8"));
const part = timing.parts[compId === "Part1" ? "part1" : "part2"];
const outDir = path.join(root, "out/stills", compId);
fs.mkdirSync(outDir, { recursive: true });

const want = sceneFilter ? sceneFilter.split(",") : null;
const frames = [];
for (const s of part.scenes) {
  if (want && !want.includes(s.id)) continue;
  if (flag === "--lines") {
    for (const l of s.lines) {
      const f = s.startFrame + Math.round((l.startFrame + (l.endFrame || l.startFrame + 30)) / 2 + 12);
      frames.push({ f, name: `${s.id}-${l.id}` });
    }
  } else {
    const a = s.startFrame + 20;
    const b = s.startFrame + Math.round(s.durationFrames / 2);
    const c = s.startFrame + s.durationFrames - 40;
    frames.push({ f: a, name: `${s.id}-a-start` }, { f: b, name: `${s.id}-b-middle` }, { f: c, name: `${s.id}-c-end` });
  }
}

const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts") });
const composition = await selectComposition({ serveUrl, id: compId, browserExecutable: process.env.REMOTION_BROWSER });
const files = [];
for (const { f, name } of frames) {
  const output = path.join(outDir, `${name}-f${f}.png`);
  await renderStill({ serveUrl, composition, frame: f, output, browserExecutable: process.env.REMOTION_BROWSER, scale: 0.5 });
  files.push(output);
}
// contact sheets of 6 (3×2)
for (let i = 0; i < files.length; i += 6) {
  const group = files.slice(i, i + 6);
  while (group.length < 6) group.push(group[group.length - 1]);
  const inputs = group.flatMap((g) => ["-i", g]);
  const filter = "[0][1][2]hstack=3[t];[3][4][5]hstack=3[u];[t][u]vstack";
  const sheet = path.join(outDir, `sheet-${String(i / 6 + 1).padStart(2, "0")}.png`);
  execFileSync("ffmpeg", ["-v", "error", "-y", ...inputs, "-filter_complex", filter, sheet]);
  console.log(sheet, group.map((g) => path.basename(g)).join(" | "));
}
