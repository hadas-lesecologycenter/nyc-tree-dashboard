import React, { useId } from "react";
import { C } from "../theme";
import { Particle, Sign } from "./ui";
import { rand } from "./anim";

const useSafeId = () => useId().replace(/[^a-zA-Z0-9]/g, "");

type M = { cx: number; cy: number; r: number };

/** Dalton: one solid ball. */
const SPHERE_COLORS = {
  a: ["#DCE6F2", C.sphere, "#4D5F79"],
  b: ["#D9F5E4", "#5FBF8A", "#2C6B4A"],
  dark: ["#8A919C", "#4A505A", "#25292F"],
};

export const SolidSphere: React.FC<M & { variant?: keyof typeof SPHERE_COLORS }> = ({ cx, cy, r, variant = "a" }) => {
  const id = useSafeId();
  const [c0, c1, c2] = SPHERE_COLORS[variant];
  return (
    <g>
      <defs>
        <radialGradient id={`ss${id}`} cx="35%" cy="32%" r="70%">
          <stop offset="0%" stopColor={c0} />
          <stop offset="55%" stopColor={c1} />
          <stop offset="100%" stopColor={c2} />
        </radialGradient>
      </defs>
      <circle cx={cx} cy={cy} r={r} fill={`url(#ss${id})`} />
    </g>
  );
};

/** Thomson: a ball of spread-out positive charge with electrons in it (NOT protons). */
export const PlumPudding: React.FC<M & { haze?: number; electrons?: boolean; signs?: boolean }> = ({
  cx,
  cy,
  r,
  haze = 1,
  electrons = true,
  signs = true,
}) => {
  const id = useSafeId();
  const e = [
    [-0.45, -0.35],
    [0.3, -0.5],
    [0.55, 0.05],
    [-0.1, 0.05],
    [-0.55, 0.3],
    [0.2, 0.5],
    [0.0, -0.75],
    [-0.2, 0.72],
  ];
  const plus = [
    [-0.2, -0.45],
    [0.6, -0.3],
    [0.22, -0.12],
    [-0.42, -0.02],
    [0.35, 0.3],
    [-0.25, 0.45],
    [0.65, 0.42],
    [-0.7, -0.4],
  ];
  return (
    <g>
      <defs>
        <radialGradient id={`pp${id}`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(229,72,77,0.55)" />
          <stop offset="80%" stopColor="rgba(229,72,77,0.38)" />
          <stop offset="100%" stopColor="rgba(229,72,77,0.18)" />
        </radialGradient>
      </defs>
      <circle cx={cx} cy={cy} r={r} fill={`url(#pp${id})`} opacity={haze} stroke="rgba(255,140,140,0.6)" strokeWidth={Math.max(1, r * 0.015)} />
      {signs &&
        plus.map(([x, y], i) => (
          <g key={i} opacity={0.75 * haze}>
            <Sign x={cx + x * r} y={cy + y * r} size={r * 0.14} plus color="#FFB3B5" />
          </g>
        ))}
      {electrons && e.map(([x, y], i) => <Particle key={i} kind="electron" x={cx + x * r} y={cy + y * r} r={r * 0.11} />)}
    </g>
  );
};

/** Electron positions on loose, crossing, non-repeating paths (Rutherford: no rings). */
export const wanderPos = (i: number, frame: number, r: number) => {
  const a = 0.011 + 0.004 * i;
  const b = 0.017 + 0.003 * ((i * 7) % 5);
  const ph = i * 2.1;
  const x = Math.sin(frame * a + ph) * 0.75 + Math.sin(frame * a * 2.3 + ph * 1.7) * 0.2;
  const y = Math.cos(frame * b + ph * 1.3) * 0.7 + Math.sin(frame * b * 1.7 + ph) * 0.2;
  // keep electrons away from the centre
  const d = Math.hypot(x, y);
  const k = d < 0.35 ? 0.35 / Math.max(d, 0.01) : 1;
  return [x * k * r, y * k * r];
};

/** Rutherford: tiny + nucleus, electrons moving on loose crossing paths, mostly empty space. */
export const NuclearModel: React.FC<M & { frame: number; electrons?: number; trails?: boolean; boundary?: boolean }> = ({
  cx,
  cy,
  r,
  frame,
  electrons = 4,
  trails = true,
  boundary = true,
}) => {
  const items = [];
  for (let i = 0; i < electrons; i++) {
    const pts: string[] = [];
    if (trails) {
      for (let k = 30; k >= 0; k -= 2) {
        const [x, y] = wanderPos(i, frame - k, r * 0.85);
        pts.push(`${cx + x},${cy + y}`);
      }
    }
    const [x, y] = wanderPos(i, frame, r * 0.85);
    items.push(
      <g key={i}>
        {trails && <polyline points={pts.join(" ")} fill="none" stroke={C.electron} strokeOpacity={0.4} strokeWidth={Math.max(1.5, r * 0.02)} strokeLinecap="round" />}
        <Particle kind="electron" x={cx + x} y={cy + y} r={Math.max(5, r * 0.08)} />
      </g>,
    );
  }
  return (
    <g>
      {boundary && <circle cx={cx} cy={cy} r={r} fill="rgba(255,255,255,0.03)" stroke={C.dim} strokeWidth={Math.max(1, r * 0.012)} strokeDasharray={`${r * 0.05} ${r * 0.05}`} />}
      <Particle kind="proton" x={cx} y={cy} r={Math.max(5, r * 0.07)} />
      {items}
    </g>
  );
};

/** Bohr: nucleus with electrons on circular rings (energy levels). */
export const PlanetaryModel: React.FC<M & { frame: number; levels?: number; electrons?: number[]; showE?: boolean }> = ({
  cx,
  cy,
  r,
  frame,
  levels = 3,
  electrons = [0, 1, 2],
  showE = true,
}) => {
  const radii = Array.from({ length: levels }, (_, i) => (r * (i + 1)) / levels);
  return (
    <g>
      {radii.map((rr, i) => (
        <circle key={i} cx={cx} cy={cy} r={rr} fill="none" stroke={C.muted} strokeOpacity={0.7} strokeWidth={Math.max(1.5, r * 0.012)} />
      ))}
      <Particle kind="proton" x={cx} y={cy} r={Math.max(5, r * 0.09)} />
      {showE &&
        electrons.map((lv, i) => {
          const rr = radii[Math.min(lv, levels - 1)];
          const a = frame * (0.03 / (lv + 1)) + i * 2.2;
          return <Particle key={i} kind="electron" x={cx + Math.cos(a) * rr} y={cy + Math.sin(a) * rr} r={Math.max(5, r * 0.075)} />;
        })}
    </g>
  );
};

/** Sample points for a 1s-like orbital cloud (dense near the centre, fading out). */
export const cloudPoint = (i: number, r: number) => {
  // radius from a gamma-like distribution, so the cloud is thickest in the middle
  const u1 = rand(i + 1) || 0.001;
  const u2 = rand(i + 1000) || 0.001;
  const rr = (-Math.log(u1 * u2) / 5.2) * r; // sum of 2 exponentials
  const a = rand(i + 5000) * Math.PI * 2;
  return [Math.cos(a) * Math.min(rr, r * 1.05), Math.sin(a) * Math.min(rr, r * 1.05)];
};

/** Schrödinger: fuzzy dot cloud around the nucleus. */
export const QuantumModel: React.FC<M & { count?: number; glow?: boolean }> = ({ cx, cy, r, count = 1000, glow = true }) => {
  const id = useSafeId();
  const dots = [];
  const dr = Math.max(1, r * 0.012);
  for (let i = 0; i < count; i++) {
    const [x, y] = cloudPoint(i, r);
    dots.push(<circle key={i} cx={cx + x} cy={cy + y} r={dr} fill={C.electron} opacity={0.85} />);
  }
  return (
    <g>
      <defs>
        <radialGradient id={`qm${id}`} cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="rgba(61,139,255,0.55)" />
          <stop offset="60%" stopColor="rgba(61,139,255,0.15)" />
          <stop offset="100%" stopColor="rgba(61,139,255,0)" />
        </radialGradient>
      </defs>
      {glow && <circle cx={cx} cy={cy} r={r * 1.05} fill={`url(#qm${id})`} />}
      {dots}
      <Particle kind="proton" x={cx} y={cy} r={Math.max(4, r * 0.06)} />
    </g>
  );
};

/** Small icon of a model, used on the timeline and in the recap. */
export const ModelIcon: React.FC<{ i: number; cx: number; cy: number; r: number; frame: number }> = ({ i, cx, cy, r, frame }) => {
  if (i === 0) return <SolidSphere cx={cx} cy={cy} r={r * 0.92} />;
  if (i === 1) return <PlumPudding cx={cx} cy={cy} r={r * 0.95} />;
  if (i === 2) return <NuclearModel cx={cx} cy={cy} r={r} frame={frame} electrons={3} trails={r > 60} boundary={false} />;
  if (i === 3) return <PlanetaryModel cx={cx} cy={cy} r={r * 0.95} frame={frame} levels={2} electrons={[0, 1]} />;
  return <QuantumModel cx={cx} cy={cy} r={r * 0.9} count={r > 60 ? 600 : 160} />;
};

export const MODELS = [
  { name: "Solid Sphere", year: "1803", who: "Dalton" },
  { name: "Plum Pudding", year: "1904", who: "Thomson" },
  { name: "Nuclear", year: "1911", who: "Rutherford" },
  { name: "Planetary", year: "1913", who: "Bohr" },
  { name: "Quantum", year: "1926", who: "Schrödinger" },
];
