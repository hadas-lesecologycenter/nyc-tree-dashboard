import React from "react";
import { AbsoluteFill, Audio, Sequence, staticFile, useCurrentFrame, interpolate } from "remotion";
import { C, FONT } from "../theme";
import { pop, prog } from "./anim";

/** Full-frame SVG canvas in 1920×1080 coordinates. */
export const Svg: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({ children, style }) => (
  <svg
    viewBox="0 0 1920 1080"
    width={1920}
    height={1080}
    style={{ position: "absolute", left: 0, top: 0, overflow: "visible", ...style }}
  >
    {children}
  </svg>
);

/** A + or − drawn with rectangles (crisp at any size). */
export const Sign: React.FC<{ x: number; y: number; size: number; plus: boolean; color: string }> = ({
  x,
  y,
  size,
  plus,
  color,
}) => {
  const w = size;
  const t = Math.max(2, size * 0.24);
  return (
    <g>
      <rect x={x - w / 2} y={y - t / 2} width={w} height={t} rx={t / 2} fill={color} />
      {plus && <rect x={x - t / 2} y={y - w / 2} width={t} height={w} rx={t / 2} fill={color} />}
    </g>
  );
};

export type Kind = "electron" | "proton" | "neutron" | "alpha" | "hydrogen";

/** Particle: electron (blue, −), proton/positive (red, +), neutron (gray, no sign), alpha (yellow, +). */
export const Particle: React.FC<{ kind: Kind; x: number; y: number; r: number; opacity?: number; glow?: boolean }> = ({
  kind,
  x,
  y,
  r,
  opacity = 1,
  glow,
}) => {
  const fill =
    kind === "electron" ? C.electron : kind === "proton" ? C.proton : kind === "alpha" ? C.alpha : C.neutron;
  const signColor = kind === "alpha" ? C.alphaSign : "#FFFFFF";
  const sign = kind === "electron" ? "minus" : kind === "proton" || kind === "alpha" ? "plus" : null;
  return (
    <g opacity={opacity}>
      {glow && <circle cx={x} cy={y} r={r * 1.9} fill={fill} opacity={0.22} />}
      <circle cx={x} cy={y} r={r} fill={fill} stroke="rgba(255,255,255,0.55)" strokeWidth={Math.max(1, r * 0.08)} />
      {sign && <Sign x={x} y={y} size={r * 1.05} plus={sign === "plus"} color={signColor} />}
    </g>
  );
};

/** Inline arrow glyph (the font has no → character). */
export const InlineArrow: React.FC<{ size: number; color?: string }> = ({ size, color = "currentColor" }) => (
  <svg width={size * 0.9} height={size * 0.6} viewBox="0 0 90 60" style={{ display: "inline-block", verticalAlign: "middle", margin: "0 0.12em" }}>
    <line x1={4} y1={30} x2={66} y2={30} stroke={color} strokeWidth={10} strokeLinecap="round" />
    <polygon points="86,30 58,10 58,50" fill={color} />
  </svg>
);

/** Renders text, drawing every "→" as an inline arrow. */
export const T: React.FC<{ s: string; size: number }> = ({ s, size }) => {
  const parts = s.split("→");
  return (
    <>
      {parts.map((p, i) => (
        <React.Fragment key={i}>
          {i > 0 && <InlineArrow size={size} />}
          {p}
        </React.Fragment>
      ))}
    </>
  );
};

/** Short on-screen label (6 words max). Key part in yellow, the rest in white. */
export const Label: React.FC<{
  x: number;
  y: number;
  start: number;
  k?: string;
  v?: string;
  size?: number;
  end?: number;
  kLast?: boolean; // show the yellow key part after the white part
}> = ({ x, y, start, k, v, size = 54, end, kLast }) => {
  const frame = useCurrentFrame();
  const s = pop(frame, start);
  const out = end !== undefined ? 1 - prog(frame, end, 8) : 1;
  if (s <= 0.001 || out <= 0) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${0.7 + 0.3 * s})`,
        opacity: Math.min(1, s * 1.4) * out,
        fontFamily: FONT,
        fontSize: size,
        fontWeight: 700,
        color: C.text,
        background: "rgba(16, 28, 46, 0.92)",
        border: `3px solid ${C.panelEdge}`,
        borderRadius: 22,
        padding: "10px 30px",
        whiteSpace: "nowrap",
        lineHeight: 1.2,
      }}
    >
      {k && !kLast && (
        <span style={{ color: C.accent }}>
          <T s={k} size={size} />
        </span>
      )}
      {k && v && !kLast ? " " : null}
      {v && <T s={v} size={size} />}
      {k && v && kLast ? " " : null}
      {k && kLast && (
        <span style={{ color: C.accent }}>
          <T s={k} size={size} />
        </span>
      )}
    </div>
  );
};

/** Plain big text (titles), no box. */
export const Title: React.FC<{ x: number; y: number; start: number; text: string; size?: number; color?: string }> = ({
  x,
  y,
  start,
  text,
  size = 72,
  color = C.text,
}) => {
  const frame = useCurrentFrame();
  const s = pop(frame, start);
  if (s <= 0.001) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${0.8 + 0.2 * s})`,
        opacity: Math.min(1, s * 1.4),
        fontFamily: FONT,
        fontSize: size,
        fontWeight: 700,
        color,
        whiteSpace: "nowrap",
        textAlign: "center",
      }}
    >
      {text}
    </div>
  );
};

/** Generic person silhouette (no portraits). */
export const Silhouette: React.FC<{ size: number }> = ({ size }) => (
  <svg width={size} height={size} viewBox="0 0 100 100">
    <circle cx={50} cy={50} r={50} fill="#2B4266" />
    <circle cx={50} cy={38} r={17} fill="#9FB0C7" />
    <path d="M18 92 C 20 66, 36 58, 50 58 C 64 58, 80 66, 82 92 Z" fill="#9FB0C7" />
  </svg>
);

/** Scientist name card: silhouette, name, country, year. */
export const NameCard: React.FC<{
  x: number;
  y: number;
  start: number;
  name: string;
  place: string;
  year?: string;
  scale?: number;
}> = ({ x, y, start, name, place, year, scale = 1 }) => {
  const frame = useCurrentFrame();
  const s = pop(frame, start);
  if (s <= 0.001) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${(0.75 + 0.25 * s) * scale})`,
        opacity: Math.min(1, s * 1.4),
        display: "flex",
        alignItems: "center",
        gap: 30,
        background: C.panel,
        border: `3px solid ${C.panelEdge}`,
        borderRadius: 28,
        padding: "26px 40px 26px 28px",
        fontFamily: FONT,
        color: C.text,
        whiteSpace: "nowrap",
        boxShadow: "0 12px 40px rgba(0,0,0,0.35)",
      }}
    >
      <Silhouette size={150} />
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <div style={{ fontSize: 56, fontWeight: 700 }}>{name}</div>
        <div style={{ fontSize: 40, color: C.muted }}>{place}</div>
        {year && <div style={{ fontSize: 44, fontWeight: 700, color: C.accent }}>{year}</div>}
      </div>
    </div>
  );
};

/** Card with a heading ("Prediction" / "Result") and short text. */
export const InfoCard: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  start: number;
  head: string;
  text?: string;
  headColor?: string;
  children?: React.ReactNode;
}> = ({ x, y, w, h, start, head, text, headColor = C.accent, children }) => {
  const frame = useCurrentFrame();
  const s = pop(frame, start);
  if (s <= 0.001) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: x - w / 2,
        top: y - h / 2,
        width: w,
        height: h,
        transform: `scale(${0.8 + 0.2 * s})`,
        opacity: Math.min(1, s * 1.4),
        background: C.panel,
        border: `3px solid ${C.panelEdge}`,
        borderRadius: 30,
        fontFamily: FONT,
        color: C.text,
        boxSizing: "border-box",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          fontSize: 50,
          fontWeight: 700,
          color: headColor,
          textAlign: "center",
          paddingTop: 22,
        }}
      >
        {head}
      </div>
      {text && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 26, textAlign: "center", fontSize: 50, fontWeight: 700 }}>
          {text}
        </div>
      )}
      {children}
    </div>
  );
};

/** "UPDATED" stamp (never "wrong"). */
export const Stamp: React.FC<{ x: number; y: number; start: number; size?: number }> = ({ x, y, start, size = 64 }) => {
  const frame = useCurrentFrame();
  if (frame < start) return null;
  const t = prog(frame, start, 8);
  const sc = interpolate(t, [0, 1], [1.8, 1]);
  return (
    <>
      <div
        style={{
          position: "absolute",
          left: x,
          top: y,
          transform: `translate(-50%, -50%) rotate(-10deg) scale(${sc})`,
          opacity: t,
          fontFamily: FONT,
          fontSize: size,
          fontWeight: 700,
          letterSpacing: 4,
          color: C.updated,
          border: `7px solid ${C.updated}`,
          borderRadius: 16,
          padding: "4px 26px",
          background: "rgba(15, 27, 45, 0.85)",
          whiteSpace: "nowrap",
        }}
      >
        UPDATED
      </div>
      <Sequence from={start} durationInFrames={20} layout="none">
        <Audio src={staticFile("sfx/stamp.wav")} volume={0.35} />
      </Sequence>
    </>
  );
};

/** Arrow (SVG) from (x1,y1) to (x2,y2). */
export const Arrow: React.FC<{
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  color?: string;
  width?: number;
  t?: number;
  dashed?: boolean;
}> = ({ x1, y1, x2, y2, color = C.text, width = 8, t = 1, dashed }) => {
  if (t <= 0) return null;
  const ex = x1 + (x2 - x1) * t;
  const ey = y1 + (y2 - y1) * t;
  const ang = Math.atan2(ey - y1, ex - x1);
  const h = width * 3.2;
  const p1 = [ex - h * Math.cos(ang - 0.45), ey - h * Math.sin(ang - 0.45)];
  const p2 = [ex - h * Math.cos(ang + 0.45), ey - h * Math.sin(ang + 0.45)];
  return (
    <g>
      <line
        x1={x1}
        y1={y1}
        x2={ex - Math.cos(ang) * h * 0.6}
        y2={ey - Math.sin(ang) * h * 0.6}
        stroke={color}
        strokeWidth={width}
        strokeLinecap="round"
        strokeDasharray={dashed ? `${width * 2} ${width * 2}` : undefined}
      />
      <polygon points={`${ex},${ey} ${p1[0]},${p1[1]} ${p2[0]},${p2[1]}`} fill={color} />
    </g>
  );
};

/** Plays the soft "pop" sound at a frame. */
export const PopSfx: React.FC<{ at: number }> = ({ at }) =>
  at < 1e8 ? (
    <Sequence from={Math.max(0, Math.round(at))} durationInFrames={12} layout="none">
      <Audio src={staticFile("sfx/pop.wav")} volume={0.18} />
    </Sequence>
  ) : null;

export const Fill: React.FC<{ children: React.ReactNode }> = ({ children }) => <AbsoluteFill>{children}</AbsoluteFill>;
