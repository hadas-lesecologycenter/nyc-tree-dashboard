import React from "react";
import { useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { useAt } from "../timing";
import { Shots } from "../components/Shots";
import { Arrow, InfoCard, Label, NameCard, Particle, Svg, Title } from "../components/ui";
import { lerp, pop, prog, rand } from "../components/anim";
import { NuclearModel, PlumPudding, SolidSphere } from "../components/models";
import { UpdateShot } from "../components/Update";

const LastTime: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s4-0");
  return (
    <>
      <Svg>
        <g opacity={pop(f, s)}>
          <SolidSphere cx={620} cy={490} r={150} />
        </g>
        <Arrow x1={820} y1={490} x2={1060} y2={490} t={prog(f, s + 30, 16)} color={C.muted} width={10} />
        <g transform={`translate(1290 490) scale(${pop(f, s + 40)}) translate(-1290 -490)`}>
          <PlumPudding cx={1290} cy={490} r={170} />
        </g>
      </Svg>
      <div style={{ position: "absolute", left: 620, top: 680, transform: "translate(-50%,-50%) rotate(-8deg)", fontFamily: FONT, fontWeight: 700, fontSize: 36, color: C.updated, border: `5px solid ${C.updated}`, borderRadius: 10, padding: "2px 16px", opacity: pop(f, s + 10) }}>
        UPDATED
      </div>
      <Label x={960} y={250} start={s + 4} k="Last time" />
    </>
  );
};

const Rutherford: React.FC = () => {
  const { at } = useAt();
  return <NameCard x={960} y={470} start={at("s4-1")} name="Ernest Rutherford" place="New Zealand" year="1911" />;
};

const Foil: React.FC<{ x: number; y: number; h: number; w?: number }> = ({ x, y, h, w = 10 }) => (
  <rect x={x - w / 2} y={y - h / 2} width={w} height={h} rx={3} fill={C.gold} stroke={C.goldLight} strokeWidth={2} />
);

const Source: React.FC<{ x: number; y: number; s?: number }> = ({ x, y, s = 1 }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <rect x={-90} y={-70} width={150} height={140} rx={12} fill="#5A6170" stroke="#7D8BA0" strokeWidth={4} />
    <rect x={20} y={-14} width={42} height={28} fill="#1B2433" />
    <circle cx={-20} cy={0} r={26} fill="#7BD34A" opacity={0.85} />
  </g>
);

const Team: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s4-2");
  const mid = s + (end("s4-2") - s) * 0.3;
  const setup = s + (end("s4-2") - s) * 0.6;
  const dots = [0, 1, 2, 3].map((i) => {
    const t = (((f - setup) * 0.03 + i * 0.25) % 1 + 1) % 1;
    return lerp(640, 1180, t);
  });
  return (
    <>
      <NameCard x={540} y={330} start={s + 4} name="Hans Geiger" place="Germany" year="1909" scale={0.76} />
      <NameCard x={1380} y={330} start={mid} name="Ernest Marsden" place="England" year="1909" scale={0.76} />
      <Svg>
        <g opacity={prog(f, setup, 12)}>
          <Source x={560} y={650} s={0.8} />
          {f > setup + 10 && dots.map((x, i) => <Particle key={i} kind="alpha" x={x} y={650} r={13} />)}
          <Foil x={1200} y={650} h={190} />
        </g>
      </Svg>
      <Label x={1480} y={650} start={setup + 14} k="gold foil" size={46} />
    </>
  );
};

const AlphaShot: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s4-3");
  const x = lerp(300, 960, prog(f, s, 36));
  return (
    <>
      <Svg>
        <defs>
          <linearGradient id="trailA" x1="0" x2="1">
            <stop offset="0" stopColor={C.alpha} stopOpacity={0} />
            <stop offset="1" stopColor={C.alpha} stopOpacity={0.6} />
          </linearGradient>
        </defs>
        <rect x={Math.max(150, x - 500)} y={450} width={Math.max(0, x - Math.max(150, x - 500))} height={60} rx={30} fill="url(#trailA)" />
        <Particle kind="alpha" x={x} y={480} r={100} glow />
      </Svg>
      <Label x={960} y={740} start={s + 30} k="alpha particle" v="(+)" />
    </>
  );
};

const Radioactive: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s4-4");
  return (
    <>
      <Svg>
        <g opacity={pop(f, s)}>
          <Source x={560} y={470} s={1.6} />
          {[0, 1, 2, 3, 4].map((i) => {
            const t = (((f - s) * 0.025 + i * 0.2) % 1 + 1) % 1;
            const x = lerp(680, 1650, t);
            return f > s + 10 ? <Particle key={i} kind="alpha" x={x} y={470} r={22} opacity={t < 0.9 ? 1 : (1 - t) * 10} /> : null;
          })}
        </g>
      </Svg>
      <Label x={960} y={740} start={s + 20} k="radioactive" v="= shoots out particles" />
    </>
  );
};

const Thin: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s4-5");
  return (
    <>
      <Svg>
        <g opacity={pop(f, s)}>
          <rect x={700} y={260} width={70} height={400} rx={4} fill="#F4F7FB" />
          <Foil x={1200} y={460} h={400} w={6} />
        </g>
      </Svg>
      <Label x={735} y={720} start={s + 8} v="paper" size={48} />
      <Label x={1200} y={720} start={s + 14} k="gold foil" size={48} />
      <Title x={960} y={250} start={s + 30} text="much thinner!" size={56} color={C.accent} />
    </>
  );
};

/** Top view: source, beam, foil and a ring-shaped screen that flashes. */
const ScreenShot: React.FC = () => {
  const f = useCurrentFrame();
  const { at, has } = useAt();
  const s6 = at("s4-6");
  const s7 = at("s4-7");
  const dim = has("s4-7") ? prog(f, s7, 20) : 0;
  const cx = 1000;
  const cy = 480;
  const R = 250;
  // one soft flash every 18 frames (under 2 per second), mostly straight ahead
  const k = Math.floor(Math.max(0, f - s6 - 20) / 18);
  const phase = (Math.max(0, f - s6 - 20) % 18) / 18;
  const ang = k % 9 === 4 ? 0.9 : k % 9 === 7 ? -0.7 : (rand(k) - 0.5) * 0.25;
  const fx = cx + Math.cos(ang) * R;
  const fy = cy + Math.sin(ang) * R;
  return (
    <>
      <Svg>
        <g opacity={pop(f, s6)}>
          <circle cx={cx} cy={cy} r={R} fill="none" stroke="#9FD8C8" strokeWidth={16} opacity={0.5} />
          <Source x={430} y={cy} s={0.9} />
          <line x1={490} y1={cy} x2={cx} y2={cy} stroke={C.alpha} strokeWidth={8} opacity={0.6} strokeDasharray="14 10" />
          <Foil x={cx} y={cy} h={150} />
          {f > s6 + 20 && <circle cx={fx} cy={fy} r={26} fill="#E8FFF6" opacity={(1 - phase) * 0.9} />}
        </g>
        <rect x={0} y={0} width={1920} height={1080} fill="#000" opacity={dim * 0.45} />
        {dim > 0 && (
          <g opacity={dim} transform={`translate(${cx + R + 40} ${cy - 40})`}>
            <rect x={-20} y={-140} width={40} height={130} rx={8} fill="#B8C4D6" />
            <rect x={-30} y={-180} width={60} height={50} rx={10} fill="#8A96AA" />
            <rect x={-12} y={-10} width={24} height={40} fill="#B8C4D6" />
            <path d="M 30 -100 Q 110 -100 110 20 L 110 80" fill="none" stroke="#8A96AA" strokeWidth={18} />
            <rect x={40} y={80} width={140} height={20} rx={6} fill="#8A96AA" />
          </g>
        )}
      </Svg>
      <Label x={cx} y={790} start={s6 + 24} k="screen" v="flashes when hit" end={s7 - 2} />
      <Label x={cx} y={790} start={s7 + 20} v="counted the flashes" />
    </>
  );
};

type Path = "straight" | "bend" | "back";
/** Position of an alpha particle (card-local coords). Foil at x=380. */
const alphaPos = (type: Path, t: number, y0: number, sign: number) => {
  const fx = 380;
  if (t < 0.5) return [lerp(30, fx, t / 0.5), y0];
  const u = (t - 0.5) / 0.5;
  if (type === "straight") return [lerp(fx, 730, u), y0];
  if (type === "bend") return [lerp(fx, 700, u), y0 + sign * lerp(0, 140, u)];
  return [lerp(fx, 60, u), y0 + sign * lerp(0, 60, u)];
};

const Alphas: React.FC<{ frame: number; types: { type: Path; y: number; sign: number; off: number }[]; speed: number }> = ({ frame, types, speed }) => (
  <g>
    {types.map((p, i) => {
      const t = (((frame * speed + p.off) % 1) + 1) % 1;
      const [x, y] = alphaPos(p.type, t, p.y, p.sign);
      const [px, py] = alphaPos(p.type, Math.max(0, t - 0.06), p.y, p.sign);
      return (
        <g key={i}>
          <line x1={px} y1={py} x2={x} y2={y} stroke={C.alpha} strokeOpacity={0.5} strokeWidth={8} strokeLinecap="round" />
          <Particle kind="alpha" x={x} y={y} r={12} />
        </g>
      );
    })}
  </g>
);

const Experiment: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s8 = at("s4-8");
  const s9 = at("s4-9");
  const s10 = at("s4-10");
  const s11 = at("s4-11");
  const s12 = at("s4-12");
  const s13 = at("s4-13");
  const s14 = at("s4-14");
  const straight = [150, 210, 270, 330, 390].map((y, i) => ({ type: "straight" as Path, y, sign: 1, off: i * 0.21 }));
  const bends = [
    { type: "bend" as Path, y: 235, sign: -1, off: 0.1 },
    { type: "bend" as Path, y: 310, sign: 1, off: 0.6 },
  ];
  const back = [{ type: "back" as Path, y: 270, sign: -1, off: 0.35 }];
  const replay = f >= s14;
  const resTypes = [...straight, ...(f >= s12 ? bends : []), ...(f >= s13 ? back : [])];
  const resText = f >= s13 ? "some bounce back!" : f >= s12 ? "a few bend" : f >= s11 ? "most go straight" : "";
  return (
    <>
      <InfoCard x={540} y={545} w={760} h={540} start={s8} head="Prediction" text={f >= s9 ? "all go straight" : "+ spread thin"}>
        <svg width={760} height={560} viewBox="0 0 760 560" style={{ position: "absolute", left: 0, top: 0 }}>
          {[150, 270, 390].map((y) => (
            <PlumPudding key={y} cx={380} cy={y} r={58} signs={false} />
          ))}
          {f >= s9 && <Alphas frame={f - s9} types={straight} speed={0.012} />}
        </svg>
      </InfoCard>
      <InfoCard x={1380} y={545} w={760} h={540} start={s10} head={replay ? "Result: replay" : "Result"} text={replay ? "slow motion" : resText} headColor={C.good}>
        <svg width={760} height={560} viewBox="0 0 760 560" style={{ position: "absolute", left: 0, top: 0 }}>
          <rect x={375} y={110} width={10} height={340} fill={C.gold} />
          {!replay && f >= s11 && <Alphas frame={f - s11} types={resTypes} speed={0.012} />}
          {replay && <Alphas frame={f - s14} types={[{ type: "back", y: 270, sign: -1, off: 0 }]} speed={1 / 95} />}
        </svg>
      </InfoCard>
      {f >= s13 && !replay && (
        <Label x={1380} y={226} start={s13 + 20} k="about 1 in 8,000" size={44} />
      )}
    </>
  );
};

const Cannon: React.FC = () => {
  const f = useCurrentFrame();
  const { at, has } = useAt();
  const s15 = at("s4-15");
  const s16 = has("s4-16") ? at("s4-16") : s15 + 60;
  const fly = prog(f, s15 + 15, Math.max(20, s16 - s15 - 20));
  const back = prog(f, s16, 30);
  const sx = back > 0 ? lerp(1290, 560, back) : lerp(560, 1290, fly);
  return (
    <>
      <Svg>
        <g opacity={pop(f, s15)}>
          <g transform="translate(420 600) rotate(-6)">
            <rect x={-60} y={-55} width={240} height={110} rx={50} fill="#4A505A" />
            <rect x={150} y={-65} width={40} height={130} rx={10} fill="#5A6170" />
          </g>
          <circle cx={420} cy={660} r={60} fill="#8B5E3C" stroke="#5E3E26" strokeWidth={10} />
          <path d="M1320 330 Q 1350 400 1320 470 Q 1290 540 1320 610 Q 1350 680 1320 740" fill="none" stroke="#F4F7FB" strokeWidth={10} opacity={0.9} />
          {f > s15 + 15 && <ellipse cx={sx} cy={580} rx={48} ry={34} fill="#9AA4B2" stroke="#D0D6DE" strokeWidth={4} />}
        </g>
      </Svg>
      <Label x={560} y={300} start={s15 + 10} v="giant shell" size={48} />
      <Label x={1320} y={260} start={s15 + 30} v="tissue paper" size={48} />
      <Label x={900} y={790} start={s16 + 20} v="it bounced back!" />
    </>
  );
};

const GoldAtom: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s17 = at("s4-17");
  const s18 = at("s4-18");
  const s19 = at("s4-19");
  const R = lerp(50, 270, prog(f, s17, 30));
  const nuc = pop(f, s18 + 10);
  const showE = f >= s19;
  return (
    <>
      <Svg>
        {!showE && (
          <circle cx={960} cy={480} r={R} fill="rgba(212,167,44,0.06)" stroke={C.gold} strokeWidth={5} strokeDasharray="20 16" />
        )}
        {!showE && nuc > 0 && (
          <g transform={`translate(960 480) scale(${nuc}) translate(-960 -480)`}>
            <Particle kind="proton" x={960} y={480} r={16} />
          </g>
        )}
        {showE && <NuclearModel cx={960} cy={480} r={270} frame={f} electrons={5} boundary={false} />}
        {showE && f > s19 + 14 && <Arrow x1={1250} y1={355} x2={985} y2={470} t={prog(f, s19 + 14, 10)} color={C.accent} width={7} />}
        {f > s18 + 30 && !showE && <Arrow x1={1180} y1={300} x2={985} y2={460} t={prog(f, s18 + 30, 10)} color={C.accent} width={7} />}
      </Svg>
      <Label x={960} y={800} start={s17 + 20} v="mostly empty space" end={s18 - 2} />
      <Label x={1340} y={270} start={s18 + 26} k="nucleus" v="= tiny center" end={s19 - 2} />
      <Label x={1450} y={330} start={s19 + 10} v="almost all the mass" size={46} />
      <Label x={1450} y={680} start={s19 + 50} v="electrons outside" size={46} />
    </>
  );
};

const Baseball: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s4-20");
  const R = lerp(40, 320, prog(f, s + 40, 30));
  return (
    <>
      <Svg>
        <g opacity={prog(f, s + 40, 6)}>
          <circle cx={900} cy={505} r={R} fill="none" stroke={C.muted} strokeWidth={5} strokeDasharray="18 14" />
        </g>
        <g transform={`translate(900 505) scale(${pop(f, s)})`}>
          <circle cx={0} cy={0} r={30} fill="#F4F7FB" />
          <path d="M -18 -22 Q -6 0 -18 22" fill="none" stroke={C.proton} strokeWidth={4} />
          <path d="M 18 -22 Q 6 0 18 22" fill="none" stroke={C.proton} strokeWidth={4} />
        </g>
      </Svg>
      <Label x={900} y={600} start={s + 10} k="nucleus" v="= baseball" size={44} />
      <Label x={1560} y={505} start={s + 70} k="atom:" v="5 miles wide" size={50} />
    </>
  );
};

const Updated2: React.FC = () => {
  const { at } = useAt();
  return <UpdateShot start={at("s4-21")} oldIndex={1} newIndex={2} newName="Nuclear Model" />;
};

const Later: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s4-22");
  return (
    <>
      <div style={{ position: "absolute", left: 960, top: 480, transform: `translate(-50%,-50%) scale(${0.8 + 0.2 * pop(f, s)})`, opacity: Math.min(1, pop(f, s) * 1.4), border: `5px dashed ${C.muted}`, borderRadius: 30, padding: "30px 80px", fontFamily: FONT, textAlign: "center", color: C.text }}>
        <div style={{ fontSize: 48, fontWeight: 700, color: C.muted }}>side note</div>
        <div style={{ fontSize: 150, fontWeight: 700, color: C.accent }}>1932</div>
      </div>
    </>
  );
};

const Proton: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s4-23");
  return (
    <>
      <Title x={960} y={260} start={s} text="hydrogen" size={60} />
      <Svg>
        <g transform={`translate(960 480) scale(${pop(f, s + 10)})`}>
          <Particle kind="proton" x={0} y={0} r={110} />
        </g>
      </Svg>
      <Label x={960} y={740} start={s + 30} k="proton" v="(+)" />
    </>
  );
};

const HeliumNuc: React.FC<{ cx: number; cy: number; f: number; neutrons: number }> = ({ cx, cy, f, neutrons }) => (
  <g>
    <Particle kind="proton" x={cx - 60} y={cy - 50} r={58} />
    <Particle kind="proton" x={cx + 60} y={cy + 50} r={58} />
    {neutrons < 1 && (
      <g opacity={1 - neutrons}>
        <circle cx={cx + 60} cy={cy - 50} r={58} fill="none" stroke={C.muted} strokeWidth={5} strokeDasharray="12 10" />
        <circle cx={cx - 60} cy={cy + 50} r={58} fill="none" stroke={C.muted} strokeWidth={5} strokeDasharray="12 10" />
        <text x={cx + 60} y={cy - 32} textAnchor="middle" fontSize={56} fontWeight={700} fill={C.muted} style={{ fontFamily: FONT }}>?</text>
        <text x={cx - 60} y={cy + 68} textAnchor="middle" fontSize={56} fontWeight={700} fill={C.muted} style={{ fontFamily: FONT }}>?</text>
      </g>
    )}
    {neutrons > 0 && (
      <g>
        <g transform={`translate(${lerp(cx + 360, cx + 60, neutrons)} ${cy - 50})`}>
          <Particle kind="neutron" x={0} y={0} r={58} />
        </g>
        <g transform={`translate(${lerp(cx - 360, cx - 60, neutrons)} ${cy + 50})`}>
          <Particle kind="neutron" x={0} y={0} r={58} />
        </g>
      </g>
    )}
  </g>
);

const Helium: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s4-24");
  return (
    <>
      <Title x={960} y={260} start={s} text="helium" size={60} />
      <Svg>
        <g transform={`translate(960 490) scale(${pop(f, s + 6)}) translate(-960 -490)`}>
          <HeliumNuc cx={960} cy={490} f={f} neutrons={0} />
        </g>
      </Svg>
      <Label x={960} y={750} start={s + 30} k="2 protons," v="4× the mass" />
    </>
  );
};

const Chadwick: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s4-25");
  const join = s + (end("s4-25") - s) * 0.5;
  return (
    <>
      <NameCard x={480} y={470} start={s} name="James Chadwick" place="England" year="1932" scale={0.8} />
      <Svg>
        <HeliumNuc cx={1350} cy={470} f={f} neutrons={prog(f, join, 26)} />
      </Svg>
      <Label x={1350} y={760} start={join + 20} k="neutron" v="= no charge" />
    </>
  );
};

export const Scene4: React.FC = () => (
  <Shots
    shots={[
      { from: "s4-0", el: <LastTime /> },
      { from: "s4-1", el: <Rutherford /> },
      { from: "s4-2", el: <Team /> },
      { from: "s4-3", el: <AlphaShot /> },
      { from: "s4-4", el: <Radioactive /> },
      { from: "s4-5", el: <Thin /> },
      { from: "s4-6", el: <ScreenShot /> },
      { from: "s4-8", el: <Experiment /> },
      { from: "s4-15", el: <Cannon /> },
      { from: "s4-17", el: <GoldAtom /> },
      { from: "s4-20", el: <Baseball /> },
      { from: "s4-21", el: <Updated2 /> },
      { from: "s4-22", el: <Later /> },
      { from: "s4-23", el: <Proton /> },
      { from: "s4-24", el: <Helium /> },
      { from: "s4-25", el: <Chadwick /> },
    ]}
  />
);

