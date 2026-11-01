import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { useAt } from "../timing";
import { Shots } from "../components/Shots";
import { Arrow, Label, NameCard, Particle, Svg } from "../components/ui";
import { pop, prog } from "../components/anim";
import { PlanetaryModel, QuantumModel, cloudPoint } from "../components/models";
import { UpdateShot } from "../components/Update";

const Check: React.FC<{ x: number; y: number; s: number }> = ({ x, y, s }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <circle r={80} fill="none" stroke={C.good} strokeWidth={10} />
    <path d="M -38 2 L -10 30 L 42 -28" fill="none" stroke={C.good} strokeWidth={16} strokeLinecap="round" strokeLinejoin="round" />
  </g>
);

const Cross: React.FC<{ x: number; y: number; s: number }> = ({ x, y, s }) => (
  <g transform={`translate(${x} ${y}) scale(${s})`}>
    <circle r={80} fill="none" stroke={C.updated} strokeWidth={10} />
    <path d="M -32 -32 L 32 32 M 32 -32 L -32 32" stroke={C.updated} strokeWidth={16} strokeLinecap="round" />
  </g>
);

const Fits: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s6-1");
  return (
    <>
      <Svg>
        <PlanetaryModel cx={760} cy={480} r={230} frame={f} levels={3} electrons={[0]} />
        <Check x={1300} y={460} s={pop(f, s + 30)} />
      </Svg>
      <Label x={1300} y={640} start={s + 34} k="hydrogen:" v="fits" />
    </>
  );
};

const Fails: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s6-2");
  const x = s + (end("s6-2") - s) * 0.55;
  return (
    <>
      <Svg>
        <PlanetaryModel cx={760} cy={480} r={230} frame={f} levels={3} electrons={[0, 0]} />
        <Check x={1300} y={460} s={1 - prog(f, x - 10, 8)} />
        <Cross x={1300} y={460} s={pop(f, x)} />
      </Svg>
      <Label x={1300} y={640} start={x + 6} k="helium:" v="doesn't fit" />
    </>
  );
};

const DeBroglie: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s6-3");
  const w = prog(f, s + (end("s6-3") - s) * 0.5, 30);
  const pts: string[] = [];
  for (let x = -220; x <= 220; x += 6) pts.push(`${1340 + x},${520 + Math.sin(x * 0.05 - f * 0.15) * 50 * w * Math.exp(-(x * x) / 30000)}`);
  return (
    <>
      <NameCard x={540} y={470} start={s} name="Louis de Broglie" place="France" year="1924" scale={0.8} />
      <Svg>
        <polyline points={pts.join(" ")} fill="none" stroke={C.electron} strokeWidth={10} strokeLinecap="round" opacity={w} />
        <Particle kind="electron" x={1340} y={520} r={60} opacity={1 - w * 0.8} />
      </Svg>
      <Label x={1340} y={720} start={s + (end("s6-3") - s) * 0.5 + 20} k="electron" v="= wave too" size={48} />
    </>
  );
};

const Schrodinger: React.FC = () => {
  const { at } = useAt();
  return <NameCard x={960} y={470} start={at("s6-4")} name="Erwin Schrödinger" place="Austria" year="1926" />;
};

const Orbital: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s6-5");
  return (
    <>
      <Svg>
        <g opacity={prog(f, s, 20)}>
          <QuantumModel cx={960} cy={480} r={240} count={500} />
        </g>
      </Svg>
      <Label x={960} y={790} start={s + 30} k="orbital" v="= likely place" />
    </>
  );
};

const Heisenberg: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s6-6");
  const t = prog(f, s + 40, 50);
  return (
    <>
      <NameCard x={540} y={470} start={s} name="Werner Heisenberg" place="Germany" year="1927" scale={0.8} />
      <Svg>
        <circle cx={1360} cy={470} r={200} fill="none" stroke={C.muted} strokeWidth={6} strokeDasharray={`${40 * (1 - t) + 2} ${10 + 60 * t}`} opacity={1 - t * 0.85} />
        <Particle kind="proton" x={1360} y={470} r={16} />
      </Svg>
      <Label x={1360} y={740} start={s + 60} k="no exact path" size={50} />
    </>
  );
};

const Snapshots: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s6-7");
  const dur = end("s6-7") - s + 30;
  const n = Math.round(interpolate(f, [s + 6, s + 6 + dur], [1, 1000], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.quad) }));
  const s8 = at("s6-8");
  const s9 = at("s6-9");
  const glow = prog(f, s8 + 10, 30);
  const cx = 960;
  const cy = 485;
  const R = 260;
  const dots = [];
  for (let i = 0; i < Math.min(n, 1000); i++) {
    const [x, y] = cloudPoint(i, R);
    dots.push(<circle key={i} cx={cx + x} cy={cy + y} r={i === n - 1 && f < s8 ? 7 : 3.4} fill={i === n - 1 && f < s8 ? "#FFFFFF" : C.electron} opacity={0.9} />);
  }
  return (
    <>
      <Svg>
        {glow > 0 && (
          <g opacity={glow}>
            <QuantumModel cx={cx} cy={cy} r={R} count={0} />
          </g>
        )}
        {dots}
        <Particle kind="proton" x={cx} y={cy} r={12} />
        {f > s9 + 20 && <Arrow x1={1340} y1={300} x2={1000} y2={455} t={prog(f, s9 + 20, 12)} color={C.accent} width={8} />}
      </Svg>
      {f < s8 + 10 && (
        <div style={{ position: "absolute", left: 1520, top: 330, transform: "translate(-50%,-50%)", fontFamily: FONT, color: C.text, textAlign: "center" }}>
          <div style={{ fontSize: 40, color: C.muted, fontWeight: 700 }}>snapshots</div>
          <div style={{ fontSize: 96, fontWeight: 700, color: C.accent }}>{n.toLocaleString("en-US")}</div>
        </div>
      )}
      <Label x={960} y={800} start={s8 + 20} k="fuzzy cloud" end={s9 - 2} />
      <Label x={1480} y={260} start={s9 + 14} k="most likely here" size={50} />
    </>
  );
};

const Updated4: React.FC = () => {
  const { at } = useAt();
  return <UpdateShot start={at("s6-10")} oldIndex={3} newIndex={4} newName="Quantum Model" />;
};

// Fun-fact lines (cut in the current version because Part 2 ran long; kept so they can be restored).
const Dad: React.FC = () => {
  const { at } = useAt();
  const s = at("s6-11");
  return (
    <>
      <NameCard x={960} y={430} start={s} name="J. J. Thomson" place="England" year="1897" />
      <Label x={960} y={700} start={s + 30} k="dad:" v="particle" />
    </>
  );
};
const Son: React.FC = () => {
  const { at } = useAt();
  const s = at("s6-12");
  return (
    <>
      <NameCard x={960} y={430} start={s} name="G. P. Thomson" place="England" year="1927" />
      <Label x={960} y={700} start={s + 30} k="son:" v="wave" />
    </>
  );
};
const Medals: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s6-13");
  const medal = (x: number, st: number) => (
    <g transform={`translate(${x} 500) scale(${pop(f, st)})`}>
      <path d="M -50 -200 L -10 -80 L 10 -80 L 50 -200" fill={C.electron} />
      <circle r={90} fill={C.gold} stroke={C.goldLight} strokeWidth={8} />
      <circle r={60} fill="none" stroke="#A57E16" strokeWidth={6} />
    </g>
  );
  return (
    <>
      <Svg>
        {medal(760, s)}
        {medal(1160, s + 10)}
      </Svg>
      <Label x={760} y={680} start={s + 20} k="dad" size={48} />
      <Label x={1160} y={680} start={s + 26} k="son" size={48} />
    </>
  );
};

export const Scene6: React.FC = () => (
  <Shots
    shots={[
      { from: "s6-1", el: <Fits /> },
      { from: "s6-2", el: <Fails /> },
      { from: "s6-3", el: <DeBroglie /> },
      { from: "s6-4", el: <Schrodinger /> },
      { from: "s6-5", el: <Orbital /> },
      { from: "s6-6", el: <Heisenberg /> },
      { from: "s6-7", el: <Snapshots /> },
      { from: "s6-10", el: <Updated4 /> },
      { from: "s6-11", el: <Dad /> },
      { from: "s6-12", el: <Son /> },
      { from: "s6-13", el: <Medals /> },
    ]}
  />
);
