import React from "react";
import { useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { PartT } from "../timing";

type Cap = { from: number; to: number; text: string };

export const buildCaptions = (part: PartT): Cap[] => {
  const caps: Cap[] = [];
  part.scenes.forEach((s) =>
    s.lines.forEach((l) => {
      if (l.silent || !l.text) return;
      caps.push({ from: s.startFrame + l.startFrame, to: s.startFrame + l.endFrame + 6, text: l.text });
    }),
  );
  // If the pause before the next line is short, keep the caption up until it starts (less flicker).
  for (let i = 0; i < caps.length - 1; i++) {
    const gap = caps[i + 1].from - caps[i].to;
    if (gap < 14) caps[i].to = caps[i + 1].from;
  }
  return caps;
};

/** Burned-in captions: large, max 2 lines, white on a solid black box, bottom of the screen. */
export const Captions: React.FC<{ caps: Cap[] }> = ({ caps }) => {
  const frame = useCurrentFrame();
  const c = caps.find((x) => frame >= x.from && frame < x.to);
  if (!c) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 34,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          maxWidth: 1660,
          background: "#000000",
          color: "#FFFFFF",
          fontFamily: FONT,
          fontSize: 54,
          fontWeight: 700,
          lineHeight: 1.22,
          padding: "14px 40px 16px",
          borderRadius: 16,
          textAlign: "center",
          border: `2px solid ${C.dim}`,
        }}
      >
        {c.text}
      </div>
    </div>
  );
};
