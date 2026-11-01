import React from "react";
import { useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { useAt } from "../timing";
import { Shots } from "../components/Shots";
import { Label, NameCard, Particle, PopSfx, Sign, Svg, Title, InfoCard } from "../components/ui";
import { lerp, pop, prog, rand } from "../components/anim";
import { PlumPudding, SolidSphere } from "../components/models";
import { Balance } from "../components/Balance";
import { UpdateShot } from "../components/Update";

// ---------- Cathode ray tube ----------
// (the object in the beam is a star, so its shadow is never confused with a + sign)
const TY = 470; // tube centre line
const X0 = 450; // beam start (cathode)
const X1 = 1470; // beam end (anode)

type TubeProps = {
  beam: number; // 0..1 how far the beam has travelled
  bend?: number; // + up, − down (pixels at the end)
  bendFrom?: number; // x where bending starts
  dots?: boolean; // beam drawn as a stream of − particles
  frame: number;
  air?: number; // 0..1 how much air has been pumped out (−1 = no air drawn)
  cross?: number; // opacity of the cross-shaped object
  plates?: number; // opacity of deflection plates
  magnet?: number; // opacity of magnet
  metal?: string;
  power?: boolean;
};

const beamY = (x: number, bend: number, from: number) => {
  if (x <= from) return TY;
  const t = (x - from) / (X1 - from);
  return TY - bend * t * t;
};

const Tube: React.FC<TubeProps> = ({ beam, bend = 0, bendFrom = 820, dots, frame, air = -1, cross = 0, plates = 0, magnet = 0, metal, power = true }) => {
  const pts: string[] = [];
  const xEnd = lerp(X0, X1, beam);
  for (let x = X0; x <= xEnd; x += 10) pts.push(`${x},${beamY(x, bend, bendFrom)}`);
  const hitY = beamY(X1, bend, bendFrom);
  return (
    <g>
      {/* power supply and wires */}
      {power && (
        <g>
          <polyline points={`430,545 430,720 860,720`} fill="none" stroke="#7D8BA0" strokeWidth={6} />
          <polyline points={`1490,545 1490,720 1060,720`} fill="none" stroke="#7D8BA0" strokeWidth={6} />
          <rect x={860} y={685} width={200} height={70} rx={12} fill="#2B3B55" stroke="#7D8BA0" strokeWidth={4} />
          <Sign x={900} y={720} size={30} plus={false} color="#FFFFFF" />
          <Sign x={1020} y={720} size={30} plus color="#FFFFFF" />
        </g>
      )}
      {/* glass */}
      <rect x={360} y={TY - 115} width={1200} height={230} rx={115} fill="rgba(200,225,255,0.07)" stroke="#CFE3FF" strokeWidth={5} />
      {/* electrodes */}
      <rect x={420} y={TY - 75} width={22} height={150} rx={6} fill="#B8C4D6" />
      <rect x={1480} y={TY - 75} width={22} height={150} rx={6} fill="#B8C4D6" />
      {/* air */}
      {air >= 0 &&
        Array.from({ length: 24 }, (_, i) => {
          const leave = i < 21 ? (i / 21) * 0.9 : 2; // last 3 stay: "most" of the air
          const t = Math.max(0, Math.min(1, (air - leave) / 0.15));
          const bx = 520 + rand(i + 7) * 880 + Math.sin(frame * 0.05 + i) * 18;
          const by = TY - 80 + rand(i + 70) * 160 + Math.cos(frame * 0.06 + i) * 12;
          const x = lerp(bx, 960, Math.min(1, t * 1.6));
          const y = t < 0.62 ? lerp(by, TY - 112, t / 0.62) : lerp(TY - 112, 270, (t - 0.62) / 0.38);
          return <circle key={i} cx={x} cy={y} r={9} fill="#CFE3FF" opacity={t >= 1 ? 0 : 0.8} />;
        })}
      {air >= 0 && (
        <g>
          <rect x={940} y={250} width={40} height={TY - 115 - 250 + 4} fill="rgba(200,225,255,0.15)" stroke="#CFE3FF" strokeWidth={4} />
        </g>
      )}
      {/* deflection plates: + on top, − below */}
      {plates > 0 && (
        <g opacity={plates}>
          <rect x={820} y={TY - 95} width={300} height={18} rx={6} fill={C.proton} />
          <rect x={820} y={TY + 77} width={300} height={18} rx={6} fill={C.electron} />
          <circle cx={1150} cy={TY - 86} r={24} fill={C.proton} />
          <Sign x={1150} y={TY - 86} size={26} plus color="#FFFFFF" />
          <circle cx={1150} cy={TY + 86} r={24} fill={C.electron} />
          <Sign x={1150} y={TY + 86} size={26} plus={false} color="#FFFFFF" />
        </g>
      )}
      {/* beam */}
      {beam > 0 && !dots && (
        <g>
          <polyline points={pts.join(" ")} fill="none" stroke="#7FD4FF" strokeWidth={30} strokeOpacity={0.25} strokeLinecap="round" />
          <polyline points={pts.join(" ")} fill="none" stroke="#BFEAFF" strokeWidth={10} strokeLinecap="round" />
        </g>
      )}
      {beam > 0 && dots &&
        Array.from({ length: 12 }, (_, i) => {
          const x = X0 + ((((frame * 9 + i * 90) % 1020) + 1020) % 1020);
          return <Particle key={i} kind="electron" x={x} y={beamY(x, bend, bendFrom)} r={16} />;
        })}
      {beam >= 1 && <ellipse cx={X1 - 6} cy={hitY} rx={16} ry={34} fill="#BFEAFF" opacity={0.8} />}
      {/* cross-shaped object */}
      {cross > 0 && (
        <g opacity={cross}>
          <polygon points="1100,408 1116,447 1159,451 1127,479 1136,520 1100,498 1064,520 1073,479 1041,451 1084,447" fill="#E8EEF6" />
        </g>
      )}
      {/* magnet: horseshoe below the tube */}
      {magnet > 0 && (
        <g opacity={magnet}>
          <path d="M880 760 L880 640 A 80 80 0 0 1 1040 640 L1040 760" fill="none" stroke="#9AA4B2" strokeWidth={50} />
          <rect x={855} y={600} width={50} height={60} fill={C.proton} />
          <rect x={1015} y={600} width={50} height={60} fill={C.electron} />
        </g>
      )}
    </g>
  );
};

const ThomsonCard: React.FC = () => {
  const { at } = useAt();
  return <NameCard x={960} y={470} start={at("s3-1")} name="J. J. Thomson" place="England" year="1897" />;
};

const TubeIntro: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s2 = at("s3-2");
  const s3 = at("s3-3");
  const s4 = at("s3-4");
  const s5 = at("s3-5");
  const s6 = at("s3-6");
  const air = prog(f, s2 + 20, 70);
  const beam = prog(f, s3 + 20, 40);
  const cross = prog(f, s5, 12);
  const shadow = prog(f, s5 + 30, 12);
  const end = beam >= 1 ? 1 : 0;
  return (
    <>
      <Svg>
        <g transform={`translate(960 520) scale(${0.85 + 0.15 * pop(f, s2)}) translate(-960 -520)`}>
          <Tube frame={f} beam={beam} air={f < s3 + 10 ? air : -1} cross={cross} />
          {/* rays past the cross edges show straight lines */}
          {f > s6 && (
            <g opacity={prog(f, s6, 12)} stroke={C.accent} strokeWidth={5} strokeDasharray="16 12">
              <line x1={X0} y1={TY} x2={X1} y2={TY - 160} />
              <line x1={X0} y1={TY} x2={X1} y2={TY + 160} />
            </g>
          )}
        </g>
        {/* end view of the far glass: glow with a sharp cross-shaped shadow */}
        {f > s5 + 26 && (
          <g opacity={shadow}>
            <circle cx={1745} cy={TY} r={110} fill="#BFEAFF" opacity={0.85 * end} />
            <circle cx={1745} cy={TY} r={110} fill="none" stroke="#CFE3FF" strokeWidth={5} />
            <polygon points="1745,392 1766,442 1819,446 1778,481 1791,533 1745,505 1699,533 1712,481 1671,446 1724,442" fill="#0F1B2D" />
          </g>
        )}
      </Svg>
      <Label x={1200} y={255} start={s2 + 30} v="air pumped out" end={s3 - 2} size={46} />
      <Label x={470} y={255} start={s3 + 30} k="cathode (−)" size={50} end={s5 - 4} />
      <Label x={1450} y={255} start={s4 + 10} k="anode (+)" size={50} end={s5 - 4} />
      <Label x={1745} y={655} start={s5 + 34} v="sharp shadow" size={42} end={s6 - 2} />
      <Label x={960} y={255} start={s6 + 8} k="straight lines" />
    </>
  );
};

const Bend: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s3-7");
  const plates = prog(f, s, 12);
  const bend = lerp(0, 120, prog(f, s + 25, 30));
  return (
    <>
      <Svg>
        <Tube frame={f} beam={1} plates={plates} bend={bend} />
      </Svg>
      <Label x={960} y={255} start={s + 40} v="bends toward" k="+" kLast />
    </>
  );
};

const Charges: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s3-8");
  const pull = s + (end("s3-8") - s) * 0.5;
  const t = prog(f, pull, 30);
  return (
    <>
      <Svg>
        <g opacity={pop(f, s)}>
          <Particle kind="proton" x={lerp(620, 885, t)} y={480} r={80} />
          <Particle kind="electron" x={lerp(1300, 1035, t)} y={480} r={70} />
        </g>
      </Svg>
      <Label x={960} y={255} start={s + 10} k="charge:" v="+ or −" />
      <Label x={960} y={740} start={pull + 6} v="opposites pull together" />
    </>
  );
};

const Particles: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s3-9");
  return (
    <>
      <Svg>
        <Tube frame={f} beam={1} dots={f > s + 20} />
      </Svg>
      <Label x={960} y={255} start={s + 40} k="particle" v="= tiny bit" />
    </>
  );
};

const Magnet: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s3-10");
  const m = prog(f, s, 12);
  const bend = lerp(0, -100, prog(f, s + 20, 26));
  return (
    <>
      <Svg>
        <Tube frame={f} beam={1} magnet={m} bend={bend} power={false} />
      </Svg>
      <Title x={880} y={630} start={s + 6} text="N" size={44} />
      <Title x={1040} y={630} start={s + 6} text="S" size={44} />
      <Label x={960} y={255} start={s + 26} k="magnet" v="bends it too" />
    </>
  );
};

const Metals: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s3-11");
  const d = end("s3-11") - s;
  const names = ["copper", "iron", "aluminum"];
  const idx = Math.min(2, Math.floor(Math.max(0, f - s - 8) / Math.max(20, (d * 0.8) / 3)));
  const colors = ["#C8773E", "#8E959E", "#C9D1DA"];
  return (
    <>
      <Svg>
        <Tube frame={f} beam={1} />
        <rect x={420} y={TY - 75} width={22} height={150} rx={6} fill={colors[idx]} />
      </Svg>
      <div key={idx}>
        <Label x={470} y={255} start={s + 8 + idx * Math.max(20, (d * 0.8) / 3)} k={names[idx]} size={50} />
      </div>
      <Label x={1300} y={255} start={s + d * 0.75} v="same beam" size={50} />
    </>
  );
};

const AtomWithE: React.FC<{ cx: number; cy: number; r: number; variant: "a" | "b" | "dark"; n: number; seed: number }> = ({ cx, cy, r, variant, n, seed }) => (
  <g>
    <g opacity={0.45}>
      <SolidSphere cx={cx} cy={cy} r={r} variant={variant} />
    </g>
    {Array.from({ length: n }, (_, i) => {
      const a = (i / n) * Math.PI * 2 + seed;
      const rr = r * (0.35 + 0.35 * rand(i + seed * 10));
      return <Particle key={i} kind="electron" x={cx + Math.cos(a) * rr} y={cy + Math.sin(a) * rr} r={r * 0.14} />;
    })}
  </g>
);

const EveryAtom: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s3-12");
  return (
    <>
      <Svg>
        {[
          { x: 520, r: 130, v: "a" as const, n: 5 },
          { x: 960, r: 110, v: "b" as const, n: 4 },
          { x: 1400, r: 150, v: "dark" as const, n: 6 },
        ].map((a, i) => (
          <g key={i} transform={`translate(${a.x} 470) scale(${pop(f, s + i * 8)}) translate(${-a.x} -470)`}>
            <AtomWithE cx={a.x} cy={470} r={a.r} variant={a.v} n={a.n} seed={i + 1} />
          </g>
        ))}
      </Svg>
      <Label x={960} y={740} start={s + 30} v="in every kind of atom" />
    </>
  );
};

const Lighter: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s3-13");
  const tilt = lerp(0, 14, prog(f, s + 30, 24));
  return (
    <>
      <Svg>
        <g opacity={pop(f, s)}>
          <Balance
            cx={960}
            tilt={tilt}
            left={(x, y) => (
              <g>
                <SolidSphere cx={x} cy={y - 62} r={58} />
              </g>
            )}
            right={(x, y) => <Particle kind="electron" x={x} y={y - 18} r={14} />}
          />
        </g>
      </Svg>
      <Label x={560} y={250} start={s + 14} v="hydrogen atom" size={44} />
      <Label x={1360} y={250} start={s + 20} v="electron" size={44} />
      <Label x={960} y={785} start={s + 50} k="1,000+ times lighter" />
    </>
  );
};

const Electron: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s3-14");
  return (
    <>
      <Svg>
        <g transform={`translate(960 450) scale(${pop(f, s)})`}>
          <Particle kind="electron" x={0} y={0} r={150} glow />
        </g>
      </Svg>
      <Label x={960} y={750} start={s + 20} k="electron" size={64} />
      <PopSfx at={s} />
    </>
  );
};

/** Side-by-side Prediction / Result cards. */
export const PredResult: React.FC<{
  s: number;
  r: number;
  predText: string;
  resText: string;
  pred: (cx: number, cy: number) => React.ReactNode;
  res: (cx: number, cy: number) => React.ReactNode;
}> = ({ s, r, predText, resText, pred, res }) => {
  const f = useCurrentFrame();
  return (
    <>
      <InfoCard x={540} y={505} w={760} h={560} start={s} head="Prediction" text={predText}>
        <svg width={760} height={560} viewBox="0 0 760 560" style={{ position: "absolute", left: 0, top: 0 }}>
          {pred(380, 270)}
        </svg>
      </InfoCard>
      <InfoCard x={1380} y={505} w={760} h={560} start={r} head="Result" text={resText} headColor={C.good}>
        <svg width={760} height={560} viewBox="0 0 760 560" style={{ position: "absolute", left: 0, top: 0 }}>
          {res(380, 270)}
        </svg>
      </InfoCard>
      {f > r + 10 && (
        <div style={{ position: "absolute", left: 960, top: 505, transform: `translate(-50%, -50%) scale(${pop(f, r + 10)})`, fontFamily: FONT, fontSize: 110, fontWeight: 700, color: C.updated }}>
          ≠
        </div>
      )}
    </>
  );
};

const Mismatch: React.FC = () => {
  const { at, end } = useAt();
  const s = at("s3-15");
  const r = s + (end("s3-15") - s) * 0.45;
  return (
    <PredResult
      s={s}
      r={r}
      predText="nothing inside"
      resText="parts inside"
      pred={(cx, cy) => <SolidSphere cx={cx} cy={cy} r={140} />}
      res={(cx, cy) => <AtomWithE cx={cx} cy={cy} r={140} variant="a" n={6} seed={2} />}
    />
  );
};

const Updated1: React.FC = () => {
  const { at } = useAt();
  return <UpdateShot start={at("s3-16")} oldIndex={0} />;
};

const Neutral: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s17 = at("s3-17");
  const s18 = at("s3-18");
  const haze = prog(f, s18 + 10, 40);
  return (
    <>
      <Svg>
        <g opacity={pop(f, s17)}>
          <circle cx={960} cy={470} r={220} fill="none" stroke={C.muted} strokeWidth={4} strokeDasharray="14 12" />
          <PlumPudding cx={960} cy={470} r={220} haze={haze} />
        </g>
      </Svg>
      <Label x={960} y={790} start={s17 + 16} k="atom:" v="no overall charge" end={s18 - 2} />
      <Label x={960} y={790} start={s18 + 30} v="something positive" k="+" kLast />
    </>
  );
};

const PlumModel: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s19 = at("s3-19");
  const s20 = at("s3-20");
  return (
    <>
      <Svg>
        <g transform={`translate(960 480) scale(${0.85 + 0.15 * pop(f, s19)}) translate(-960 -480)`}>
          <PlumPudding cx={960} cy={480} r={230} />
        </g>
      </Svg>
      <Label x={960} y={790} start={s19 + 30} k="Plum Pudding model" end={s20 - 2} />
      <Label x={960} y={790} start={s20 + 20} v="electrons in spread-out" k="+ charge" kLast />
    </>
  );
};

const Muffin: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s3-21");
  const x = 1330;
  const y = 480;
  return (
    <>
      <Svg>
        <PlumPudding cx={620} cy={470} r={210} />
        <g transform={`translate(${x} ${y}) scale(${pop(f, s + 6)}) translate(${-x} ${-y})`}>
          <path d={`M${x - 150} ${y} L${x + 150} ${y} L${x + 115} ${y + 170} L${x - 115} ${y + 170} Z`} fill="#C9844C" />
          {[-90, -45, 0, 45, 90].map((dx) => (
            <line key={dx} x1={x + dx} y1={y + 5} x2={x + dx * 0.78} y2={y + 168} stroke="#A9672F" strokeWidth={6} />
          ))}
          <path d={`M${x - 175} ${y + 8} C ${x - 190} ${y - 150}, ${x + 190} ${y - 150}, ${x + 175} ${y + 8} Z`} fill="#E8B678" />
          {[
            [-90, -40],
            [-20, -80],
            [60, -50],
            [110, -10],
            [-130, -5],
            [10, -20],
          ].map(([dx, dy], i) => (
            <Particle key={i} kind="electron" x={x + dx} y={y + dy} r={20} />
          ))}
        </g>
      </Svg>
      <Label x={960} y={790} start={s + 26} k="blueberries" v="= electrons" />
    </>
  );
};

const Dessert: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s3-22");
  return (
    <>
      <Svg>
        <g transform={`translate(960 480) scale(${pop(f, s)}) translate(-960 -480)`}>
          <ellipse cx={960} cy={600} rx={270} ry={36} fill="#E8EEF6" />
          <path d="M740 590 C 740 330, 1180 330, 1180 590 Z" fill="#6B3A22" />
          <path d="M800 420 C 860 380, 1060 380, 1120 420 C 1100 455, 1080 430, 1060 460 C 1040 430, 1000 470, 980 440 C 950 470, 920 430, 900 460 C 870 430, 840 460, 800 420 Z" fill="#F4E9D8" />
          {[
            [850, 520],
            [920, 480],
            [1010, 530],
            [1090, 500],
            [960, 560],
          ].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r={14} fill="#3A1F12" />
          ))}
        </g>
      </Svg>
      <Label x={960} y={780} start={s + 20} k="plum pudding" v="= British dessert" />
    </>
  );
};

const NextTime: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s3-23");
  return (
    <>
      <Svg>
        <g transform={`translate(960 430) scale(${pop(f, s + 6)}) translate(-960 -430)`}>
          <defs>
            <linearGradient id="foilNext" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor={C.goldLight} />
              <stop offset="0.5" stopColor={C.gold} />
              <stop offset="1" stopColor="#A57E16" />
            </linearGradient>
          </defs>
          <path d="M800 290 L1120 270 L1130 570 L790 590 Z" fill="url(#foilNext)" />
          <path d="M800 290 L1120 270 L1110 300 L812 318 Z" fill="#FFF3C4" opacity={0.5} />
        </g>
      </Svg>
      <Label x={960} y={735} start={s + 16} k="Next:" v="gold foil" size={64} />
    </>
  );
};

export const Scene3: React.FC = () => (
  <Shots
    shots={[
      { from: "s3-1", el: <ThomsonCard /> },
      { from: "s3-2", el: <TubeIntro /> },
      { from: "s3-7", el: <Bend /> },
      { from: "s3-8", el: <Charges /> },
      { from: "s3-9", el: <Particles /> },
      { from: "s3-10", el: <Magnet /> },
      { from: "s3-11", el: <Metals /> },
      { from: "s3-12", el: <EveryAtom /> },
      { from: "s3-13", el: <Lighter /> },
      { from: "s3-14", el: <Electron /> },
      { from: "s3-15", el: <Mismatch /> },
      { from: "s3-16", el: <Updated1 /> },
      { from: "s3-17", el: <Neutral /> },
      { from: "s3-19", el: <PlumModel /> },
      { from: "s3-21", el: <Muffin /> },
      { from: "s3-22", el: <Dessert /> },
      { from: "s3-23", el: <NextTime /> },
    ]}
  />
);
