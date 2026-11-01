import React from "react";
import { useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { useAt } from "../timing";
import { Shots } from "../components/Shots";
import { Label, NameCard, Particle, Svg, Title } from "../components/ui";
import { lerp, pop, prog } from "../components/anim";
import { NuclearModel } from "../components/models";
import { UpdateShot } from "../components/Update";

const H_LINES = [
  { nm: 410, color: "#9B4DFF" },
  { nm: 434, color: "#6A5BFF" },
  { nm: 486, color: "#3FD0FF" },
  { nm: 656, color: "#FF3B30" },
];

const Where: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-1");
  return (
    <>
      <Svg>
        <NuclearModel cx={860} cy={490} r={250} frame={f + 400} electrons={4} />
      </Svg>
      <Title x={1340} y={470} start={s + 10} text="?" size={220} color={C.accent} />
    </>
  );
};

const Spiral: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-2");
  const pts: string[] = [];
  for (let a = 0; a < Math.PI * 6; a += 0.1) {
    const r = 260 * (1 - a / (Math.PI * 6)) + 20;
    pts.push(`${960 + Math.cos(a) * r},${490 + Math.sin(a) * r}`);
  }
  const t = prog(f, s + 10, 80);
  const a = t * Math.PI * 6;
  const r = 260 * (1 - t) + 20;
  return (
    <>
      <Svg>
        <polyline points={pts.join(" ")} fill="none" stroke={C.muted} strokeWidth={4} strokeDasharray="10 10" opacity={0.7} />
        <Particle kind="proton" x={960} y={490} r={20} />
        <Particle kind="electron" x={960 + Math.cos(a) * r} y={490 + Math.sin(a) * r} r={22} />
      </Svg>
      <Label x={1450} y={280} start={s + 40} k="crash?" size={60} />
    </>
  );
};

const Light: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-3");
  const glow = prog(f, s + 10, 30);
  return (
    <>
      <div style={{ position: "absolute", inset: 0, background: "#050A12", opacity: 0.55 }} />
      <Svg>
        <circle cx={960} cy={440} r={200} fill="#FFE9A8" opacity={0.12 * glow} />
        <circle cx={960} cy={420} r={110} fill="#FFE9A8" opacity={0.2 + 0.7 * glow} />
        <rect x={915} y={520} width={90} height={80} rx={10} fill="#8A96AA" />
        <rect x={925} y={600} width={70} height={30} rx={10} fill="#5A6170" />
      </Svg>
      <Label x={960} y={760} start={s + 24} k="clue:" v="light" />
    </>
  );
};

const HTube: React.FC<{ x: number; y: number; w: number; glow: number }> = ({ x, y, w, glow }) => (
  <g>
    <rect x={x - w / 2 - 40} y={y - 70} width={w + 80} height={140} rx={70} fill="rgba(200,225,255,0.06)" stroke="#CFE3FF" strokeWidth={5} />
    <rect x={x - w / 2} y={y - 22} width={w} height={44} rx={22} fill="#E07BFF" opacity={0.15 + 0.75 * glow} />
    <rect x={x - w / 2 - 40} y={y - 120} width={w + 80} height={240} rx={120} fill="#E07BFF" opacity={0.12 * glow} />
    <rect x={x - w / 2 - 20} y={y - 40} width={14} height={80} rx={4} fill="#B8C4D6" />
    <rect x={x + w / 2 + 6} y={y - 40} width={14} height={80} rx={4} fill="#B8C4D6" />
  </g>
);

const Hydrogen: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-4");
  return (
    <>
      <Svg>
        <polyline points="690,480 650,480 650,680 880,680" fill="none" stroke="#7D8BA0" strokeWidth={6} />
        <polyline points="1230,480 1270,480 1270,680 1040,680" fill="none" stroke="#7D8BA0" strokeWidth={6} />
        <rect x={880} y={650} width={160} height={60} rx={10} fill="#2B3B55" stroke="#7D8BA0" strokeWidth={4} />
        <path d="M955 660 L940 685 L960 685 L948 705" fill="none" stroke={C.accent} strokeWidth={5} />
        <HTube x={960} y={480} w={500} glow={prog(f, s + 30, 20)} />
      </Svg>
      <Label x={960} y={290} start={s + 30} k="hydrogen" v="gas glows" />
    </>
  );
};

const Prism: React.FC<{ cx: number; cy: number; s?: number }> = ({ cx, cy, s = 1 }) => (
  <polygon points={`${cx},${cy - 150 * s} ${cx + 130 * s},${cy + 90 * s} ${cx - 130 * s},${cy + 90 * s}`} fill="rgba(200,225,255,0.18)" stroke="#CFE3FF" strokeWidth={5} />
);

const PrismShot: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-5");
  return (
    <>
      <Svg>
        <g transform={`translate(960 480) scale(${pop(f, s)}) translate(-960 -480)`}>
          <Prism cx={960} cy={480} s={1.3} />
        </g>
      </Svg>
      <Label x={960} y={760} start={s + 30} k="prism" v="= splits light" />
    </>
  );
};

const Rainbow: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-6");
  const t = prog(f, s + 10, 24);
  const cols = ["#FF3B30", "#FF9500", "#FFD60A", "#34C759", "#3FD0FF", "#5856D6", "#9B4DFF"];
  return (
    <>
      <Svg>
        <defs>
          <linearGradient id="rb" x1="0" y1="0" x2="0" y2="1">
            {cols.map((c, i) => (
              <stop key={i} offset={i / (cols.length - 1)} stopColor={c} />
            ))}
          </linearGradient>
        </defs>
        <line x1={250} y1={500} x2={720} y2={470} stroke="#FFFFFF" strokeWidth={14} strokeLinecap="round" />
        <Prism cx={760} cy={480} s={0.9} />
        <polygon points={`800,480 1240,${lerp(480, 330, t)} 1240,${lerp(480, 630, t)}`} fill="url(#rb)" opacity={0.3 * t} />
        <rect x={1240} y={330} width={140} height={300} fill="url(#rb)" opacity={t} />
      </Svg>
      <Label x={360} y={400} start={s + 4} k="white light" size={48} />
      <Label x={1310} y={720} start={s + 40} v="full rainbow" size={48} />
    </>
  );
};

/** Spectrum band, 400–700 nm. */
const Band: React.FC<{ x: number; y: number; w: number; h: number; lit?: number[]; labels?: boolean; all?: boolean }> = ({ x, y, w, h, lit, labels, all = true }) => {
  const px = (nm: number) => x + ((nm - 400) / 300) * w;
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} fill="#05070B" stroke={C.dim} strokeWidth={3} />
      {H_LINES.map((l, i) => {
        const on = all || (lit && lit.includes(l.nm));
        return (
          <g key={l.nm}>
            <rect x={px(l.nm) - 5} y={y} width={10} height={h} fill={l.color} opacity={on ? 1 : 0.15} />
            {on && <rect x={px(l.nm) - 14} y={y} width={28} height={h} fill={l.color} opacity={0.25} />}
            {labels && on && (
              <text x={px(l.nm)} y={i === 0 ? y - 18 : y + h + 46} textAnchor="middle" fontSize={36} fontWeight={700} fill={C.text} style={{ fontFamily: FONT }}>
                {l.nm} nm
              </text>
            )}
          </g>
        );
      })}
    </g>
  );
};

const FourLines: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-7");
  return (
    <>
      <Svg>
        <g opacity={prog(f, s, 14)}>
          <Band x={360} y={390} w={1200} h={140} labels />
        </g>
      </Svg>
      <Label x={960} y={270} start={s + 10} k="hydrogen:" v="only 4 lines" />
    </>
  );
};

const Fingerprint: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-8");
  return (
    <>
      <Svg>
        <g transform={`translate(560 470) scale(${pop(f, s)})`} fill="none" stroke="#CFE3FF" strokeWidth={9} strokeLinecap="round">
          {[30, 60, 90, 120, 150].map((r, i) => (
            <path key={r} d={`M ${-r} ${20 + i * 6} A ${r} ${r * 1.25} 0 0 1 ${r} ${10 + i * 4}`} />
          ))}
          <path d="M -150 60 Q -150 150 -90 190" />
          <path d="M 150 50 Q 150 140 100 190" />
        </g>
        <g opacity={prog(f, s + 20, 14)}>
          <Band x={900} y={420} w={760} h={110} />
        </g>
      </Svg>
      <Label x={1280} y={330} start={s + 20} v="hydrogen" size={44} />
      <Label x={960} y={760} start={s + 34} k="each element:" v="own lines" />
    </>
  );
};

const Flames: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s5-9");
  const d = end("s5-9") - s;
  const items = [
    { n: "sodium", c: "yellow-orange", col: "#FFB000" },
    { n: "lithium", c: "red", col: "#E8263B" },
    { n: "potassium", c: "violet", col: "#A35BFF" },
    { n: "barium", c: "green", col: "#7BD34A" },
  ];
  return (
    <>
      <Svg>
        {items.map((it, i) => {
          const x = 420 + i * 360;
          const y = 470;
          const w = Math.sin((f + i * 20) * 0.12) * 6;
          return (
            <g key={i} transform={`translate(${x} ${y}) scale(${pop(f, s + i * 6 + d * 0.2)})`}>
              <path d={`M 0 -150 C ${70 + w} -60, 80 70, 0 80 C -80 70, ${-70 + w} -40, -20 -80 C -15 -40, 0 -40, 0 -150 Z`} fill={it.col} />
              <path d="M 0 -20 C 30 10, 30 60, 0 65 C -30 60, -30 20, 0 -20 Z" fill="#FFFFFF" opacity={0.45} />
              <rect x={-50} y={90} width={100} height={18} rx={8} fill="#5A6170" />
            </g>
          );
        })}
      </Svg>
      {items.map((it, i) => (
        <React.Fragment key={i}>
          <Label x={420 + i * 360} y={650} start={s + i * 6 + d * 0.2 + 6} k={it.n} size={44} />
          <Title x={420 + i * 360} y={730} start={s + i * 6 + d * 0.2 + 10} text={it.c} size={36} color={C.muted} />
        </React.Fragment>
      ))}
    </>
  );
};

const Bohr: React.FC = () => {
  const { at } = useAt();
  return <NameCard x={960} y={470} start={at("s5-10")} name="Niels Bohr" place="Denmark" year="1913" />;
};

const RADII = [55, 110, 165, 220, 275];

const Rings: React.FC<{ cx: number; cy: number; n: number; labels?: boolean; litLevel?: number }> = ({ cx, cy, n, labels, litLevel }) => (
  <g>
    {RADII.slice(0, n).map((r, i) => (
      <g key={i}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={litLevel === i + 1 ? C.accent : C.muted} strokeOpacity={0.75} strokeWidth={4} />
        {labels && (
          <text x={cx + r * 0.71 + 8} y={cy - r * 0.71 - 8} fontSize={30} fontWeight={700} fill={C.text} style={{ fontFamily: FONT }}>
            {i + 1}
          </text>
        )}
      </g>
    ))}
    <Particle kind="proton" x={cx} y={cy} r={20} />
  </g>
);

const Levels: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-11");
  const a = f * 0.02;
  return (
    <>
      <Svg>
        <g opacity={prog(f, s, 14)}>
          <Rings cx={760} cy={490} n={3} labels />
          <Particle kind="electron" x={760 + Math.cos(a) * 110} y={490 + Math.sin(a) * 110} r={18} />
        </g>
      </Svg>
      <Label x={1420} y={420} start={s + 20} v="levels n = 1, 2, 3" size={48} />
      <Label x={1420} y={540} start={s + 50} k="fixed energy" size={48} />
    </>
  );
};

const Stairs: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s5-12");
  const steps = 4;
  const stepW = 180;
  const stepH = 110;
  const x0 = 520;
  const y0 = 740;
  // figure hops up one step every 40 frames
  const k = Math.min(steps - 1, Math.floor(Math.max(0, f - s - 20) / 40));
  const ph = Math.max(0, f - s - 20) % 40;
  const hopping = k < steps - 1 && ph > 26;
  const hop = hopping ? (ph - 26) / 14 : 0;
  const sx = x0 + stepW * (k + hop) + stepW / 2;
  const sy = y0 - stepH * (k + 1 + (hopping ? hop : 0)) - Math.sin(hop * Math.PI) * 60;
  const path = Array.from({ length: steps }, (_, i) => `L ${x0 + stepW * i} ${y0 - stepH * (i + 1)} L ${x0 + stepW * (i + 1)} ${y0 - stepH * (i + 1)}`).join(" ");
  return (
    <>
      <Svg>
        <path d={`M ${x0} ${y0} ${path} L ${x0 + stepW * steps} ${y0} Z`} fill="#2B3B55" stroke="#7D8BA0" strokeWidth={5} />
        <g transform={`translate(${sx} ${sy})`}>
          <circle cx={0} cy={-90} r={22} fill={C.accent} />
          <rect x={-16} y={-66} width={32} height={50} rx={12} fill={C.accent} />
          <rect x={-14} y={-20} width={10} height={20} rx={4} fill={C.accent} />
          <rect x={4} y={-20} width={10} height={20} rx={4} fill={C.accent} />
        </g>
      </Svg>
      <Label x={1460} y={330} start={s + 10} v="on a step" size={50} />
      <Label x={1460} y={440} start={s + 50} k="never between" size={50} />
    </>
  );
};

/** Electron jumping between levels; light waves fly off toward the spectrum band. */
const Jumps: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s13 = at("s5-13");
  const s14 = at("s5-14");
  const s15 = at("s5-15");
  const s16 = at("s5-16");
  const cx = 600;
  const cy = 505;
  // level as a function of time
  type Ev = { t: number; from: number; to: number; wave?: string };
  const evs: Ev[] = [
    { t: s13 + 30, from: 2, to: 3 },
    { t: s14 + 25, from: 3, to: 2, wave: "#FF3B30" },
    { t: s15 + 10, from: 2, to: 3 },
    { t: s15 + 45, from: 3, to: 2, wave: "#FF3B30" },
    { t: s16 + 10, from: 2, to: 5 },
    { t: s16 + 50, from: 5, to: 2, wave: "#9B4DFF" },
  ];
  let r = RADII[1];
  let energyIn: number | null = null;
  for (const e of evs) {
    if (f >= e.t) {
      const p = prog(f, e.t, 10);
      r = lerp(RADII[e.from - 1], RADII[e.to - 1], p);
      if (e.to > e.from && f < e.t + 4) energyIn = e.t;
    }
  }
  const a = -Math.PI / 4 + f * 0.012;
  const ex = cx + Math.cos(a) * r;
  const ey = cy + Math.sin(a) * r;
  const lit: number[] = [];
  if (f >= s15 + 70) lit.push(656);
  if (f >= s16 + 75) lit.push(434);
  const waves = evs
    .filter((e) => e.wave && f >= e.t && f < e.t + 50)
    .map((e, i) => {
      const t = (f - e.t) / 50;
      const x0 = lerp(cx + 120, 1080, t);
      const pts: string[] = [];
      for (let k = 0; k <= 40; k++) {
        const x = x0 + k * 5;
        pts.push(`${x},${cy - 120 + Math.sin(k * 0.6) * 18}`);
      }
      return <polyline key={i} points={pts.join(" ")} fill="none" stroke={e.wave} strokeWidth={8} strokeLinecap="round" opacity={1 - t * 0.3} />;
    });
  const upArrows = evs.filter((e) => e.to > e.from && f >= e.t - 20 && f < e.t + 6);
  const label3 = f >= s15 && f < s16;
  const label5 = f >= s16;
  return (
    <>
      <Svg>
        <Rings cx={cx} cy={cy} n={5} labels />
        <Particle kind="electron" x={ex} y={ey} r={18} />
        {upArrows.map((e, i) => (
          <path key={i} d={`M ${ex - 160} ${ey - 120} L ${ex - 90} ${ey - 60} L ${ex - 110} ${ey - 40} L ${ex - 30} ${ey - 10}`} fill="none" stroke={C.accent} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" opacity={prog(f, e.t - 20, 8)} />
        ))}
        {waves}
        <Band x={1100} y={300} w={680} h={120} all={false} lit={lit} labels />
      </Svg>
      <Label x={1440} y={640} start={s13 + 40} k="excited" v="= jumped up" size={48} end={s14 - 2} />
      <Label x={1440} y={640} start={s14 + 30} v="gives off light" size={48} end={s15 - 2} />
      {label3 && <Label x={1440} y={660} start={s15 + 50} k="3 → 2:" v="red" size={50} end={s16 - 2} />}
      {label5 && <Label x={1440} y={660} start={s16 + 55} k="5 → 2:" v="violet, more energy" size={46} />}
    </>
  );
};

const Updated3: React.FC = () => {
  const { at } = useAt();
  return <UpdateShot start={at("s5-17")} oldIndex={2} newIndex={3} newName="Planetary Model" />;
};

export const Scene5: React.FC = () => (
  <Shots
    shots={[
      { from: "s5-1", el: <Where /> },
      { from: "s5-2", el: <Spiral /> },
      { from: "s5-3", el: <Light /> },
      { from: "s5-4", el: <Hydrogen /> },
      { from: "s5-5", el: <PrismShot /> },
      { from: "s5-6", el: <Rainbow /> },
      { from: "s5-7", el: <FourLines /> },
      { from: "s5-8", el: <Fingerprint /> },
      { from: "s5-9", el: <Flames /> },
      { from: "s5-10", el: <Bohr /> },
      { from: "s5-11", el: <Levels /> },
      { from: "s5-12", el: <Stairs /> },
      { from: "s5-13", el: <Jumps /> },
      { from: "s5-17", el: <Updated3 /> },
    ]}
  />
);

