import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Atkinson Hyperlegible (Google Fonts, SIL Open Font License), bundled locally in public/fonts.
const FAMILY = "Atkinson Hyperlegible";
loadFont({ family: FAMILY, url: staticFile("fonts/AtkinsonHyperlegible-Regular.ttf"), weight: "400" });
loadFont({ family: FAMILY, url: staticFile("fonts/AtkinsonHyperlegible-Bold.ttf"), weight: "700" });

export const FONT = `"${FAMILY}", sans-serif`;

export const C = {
  bg: "#0F1B2D",
  bg2: "#16263D",
  panel: "#1C2E48",
  panelEdge: "#3A5579",
  text: "#F4F7FB",
  muted: "#9FB0C7",
  dim: "#4A5E7A",
  accent: "#FFD166", // labels, highlights
  electron: "#3D8BFF",
  proton: "#E5484D",
  positiveHaze: "rgba(229, 72, 77, 0.32)",
  neutron: "#9AA4B2",
  alpha: "#FFC93C",
  alphaSign: "#3A2A00",
  gold: "#D4A72C",
  goldLight: "#F2CF63",
  sphere: "#8FA3BF",
  updated: "#FFB547",
  good: "#4CD38A",
};

// Layout safe area: the timeline bar sits on top (0–165 px) and captions sit at the bottom (from about 870 px).
export const SAFE = { top: 175, bottom: 860, cx: 960, cy: 515 };
