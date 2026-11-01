import React from "react";
import { interpolateColors, useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { useAt } from "../timing";
import { Shots } from "../components/Shots";
import { InfoCard, Label, NameCard, PopSfx, Svg, Title } from "../components/ui";
import { lerp, pop, prog } from "../components/anim";
import { SolidSphere } from "../components/models";
import { Balance } from "../components/Balance";

const Laws: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s2-1");
  const tablet = (x: number, n: string, st: number) => (
    <g transform={`translate(${x} 420) scale(${pop(f, st)}) translate(${-x} -420)`}>
      <rect x={x - 130} y={260} width={260} height={320} rx={40} fill={C.panel} stroke={C.accent} strokeWidth={6} />
      <rect x={x - 80} y={430} width={160} height={14} rx={7} fill={C.muted} opacity={0.6} />
      <rect x={x - 80} y={470} width={120} height={14} rx={7} fill={C.muted} opacity={0.6} />
      <rect x={x - 80} y={510} width={140} height={14} rx={7} fill={C.muted} opacity={0.6} />
      <text x={x} y={390} textAnchor="middle" fontSize={110} fontWeight={700} fill={C.accent} style={{ fontFamily: FONT }}>
        {n}
      </text>
    </g>
  );
  return (
    <>
      <Svg style={{ fontFamily: FONT }}>
        {tablet(760, "1", s + 30)}
        {tablet(1160, "2", s + 40)}
      </Svg>
      <Label x={960} y={740} start={s + 50} k="law" v="= a rule nature follows" />
    </>
  );
};

const Jar: React.FC<{ x: number; y: number; t: number; frame: number }> = ({ x, y, t, frame }) => {
  const liquid = interpolateColors(t, [0, 1], ["#3D8BFF", "#FF8A3D"]);
  return (
    <g>
      <rect x={x - 62} y={y - 175} width={124} height={170} rx={20} fill="rgba(200,225,255,0.12)" stroke="#CFE3FF" strokeWidth={5} />
      <rect x={x - 70} y={y - 195} width={140} height={26} rx={8} fill="#B8C4D6" />
      <rect x={x - 56} y={y - 95} width={112} height={84} rx={14} fill={liquid} opacity={0.85} />
      {t > 0 && t < 1 &&
        [0, 1, 2].map((i) => {
          const k = ((frame + i * 9) % 26) / 26;
          return <circle key={i} cx={x - 25 + i * 25} cy={y - 20 - k * 70} r={7} fill="#FFFFFF" opacity={0.7 * (1 - k)} />;
        })}
    </g>
  );
};

const Weight: React.FC<{ x: number; y: number; w?: number; h?: number; color?: string }> = ({ x, y, w = 120, h = 90, color = "#9AA4B2" }) => (
  <g>
    <polygon points={`${x - w / 2},${y - 4} ${x + w / 2},${y - 4} ${x + w / 2 - 16},${y - 4 - h} ${x - w / 2 + 16},${y - 4 - h}`} fill={color} />
    <rect x={x - 16} y={y - h - 22} width={32} height={20} rx={8} fill={color} />
  </g>
);

const Lavoisier: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s2-2");
  const react = s + (end("s2-2") - s) * 0.55;
  const t = prog(f, react, 40);
  const s3 = at("s2-3");
  const cardOut = 1 - prog(f, s3 - 4, 10);
  return (
    <>
      <div style={{ opacity: cardOut }}>
        <NameCard x={470} y={470} start={s + 6} name="Antoine Lavoisier" place="France" scale={0.8} />
      </div>
      <Svg>
        <g transform={`translate(1250 520) scale(${pop(f, s + 20)}) translate(-1250 -520)`}>
          <Balance cx={1250} tilt={0} left={(x, y) => <Jar x={x} y={y} t={t} frame={f} />} right={(x, y) => <Weight x={x} y={y} />} />
        </g>
      </Svg>
      <Label x={1250} y={225} start={react} v="sealed jar" end={s3 - 4} size={46} />
      <Label x={1250} y={790} start={s3 + 4} k="mass" v="= how much stuff" />
      <Label x={470} y={470} start={s3 + 26} k="before = after" size={60} />
    </>
  );
};

const Proust: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s2-4");
  const water = s + (end("s2-4") - s) * 0.4;
  const tilt = lerp(0, 9, prog(f, water + 10, 24));
  const a = (tilt * Math.PI) / 180;
  const lx = 1250 - 270 * Math.cos(a);
  const ly = 360 + 270 * Math.sin(a) + 170;
  const rx = 1250 + 270 * Math.cos(a);
  const ry = 360 - 270 * Math.sin(a) + 170;
  return (
    <>
      <NameCard x={470} y={470} start={s + 6} name="Joseph Proust" place="France" year="late 1790s" scale={0.8} />
      <Svg>
        <g transform={`translate(1250 520) scale(${pop(f, s + 20)}) translate(-1250 -520)`}>
          <Balance
            cx={1250}
            tilt={tilt}
            left={(x, y) => (f > water ? <Weight x={x} y={y} w={150} h={120} color="#E8EEF6" /> : null)}
            right={(x, y) => (f > water ? <Weight x={x} y={y} w={70} h={40} color="#B8D8FF" /> : null)}
          />
        </g>
      </Svg>
      <Label x={lx - 40} y={765} start={water + 4} k="8 g" v="oxygen" size={46} />
      <Label x={rx + 40} y={765} start={water + 10} k="1 g" v="hydrogen" size={46} />
      <Label x={1250} y={235} start={water - 10} v="water" size={46} />
    </>
  );
};

const Dalton: React.FC = () => {
  const { at } = useAt();
  return <NameCard x={960} y={470} start={at("s2-5")} name="John Dalton" place="England" year="1803" />;
};

const OneBall: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s2-6");
  return (
    <>
      <Svg>
        <g transform={`translate(960 460) scale(${pop(f, s + 8)})`}>
          <SolidSphere cx={0} cy={0} r={190} />
        </g>
      </Svg>
      <Label x={960} y={770} start={s + 30} v="tiny solid ball" />
      <PopSfx at={s + 8} />
    </>
  );
};

const Rows: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s2-7");
  const balls = [];
  for (let r = 0; r < 3; r++)
    for (let c = 0; c < 7; c++)
      balls.push(
        <g key={`${r}-${c}`} transform={`translate(${600 + c * 120} ${310 + r * 130}) scale(${pop(f, s + (r * 7 + c) * 2)})`}>
          <SolidSphere cx={0} cy={0} r={48} />
        </g>,
      );
  return (
    <>
      <Svg>{balls}</Svg>
      <Label x={960} y={770} start={s + 40} k="element" v="= one pure substance" />
    </>
  );
};

const Join: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s2-8");
  const d = end("s2-8") - s;
  const t1 = prog(f, s + 10, 16);
  const t2 = prog(f, s + d * 0.35, 16);
  const tHalf = s + d * 0.65;
  return (
    <>
      <Svg>
        {/* 1 : 1 */}
        <g opacity={pop(f, s)}>
          <SolidSphere cx={lerp(330, 430, t1)} cy={450} r={60} />
          <SolidSphere cx={lerp(640, 530, t1)} cy={450} r={42} variant="b" />
        </g>
        {/* 1 : 2 */}
        <g opacity={pop(f, s + d * 0.3)}>
          <SolidSphere cx={960} cy={450} r={60} />
          <SolidSphere cx={lerp(1150, 1062, t2)} cy={lerp(330, 410, t2)} r={42} variant="b" />
          <SolidSphere cx={lerp(770, 858, t2)} cy={lerp(330, 410, t2)} r={42} variant="b" />
        </g>
        {/* never half an atom */}
        {f > tHalf && (
          <g opacity={prog(f, tHalf, 10)}>
            <path d="M1430 390 A 60 60 0 0 1 1430 510 Z" fill={C.sphere} />
            <line x1={1380} y1={380} x2={1500} y2={520} stroke={C.updated} strokeWidth={14} strokeLinecap="round" />
            <line x1={1500} y1={380} x2={1380} y2={520} stroke={C.updated} strokeWidth={14} strokeLinecap="round" />
          </g>
        )}
      </Svg>
      <Label x={480} y={640} start={s + 22} k="1 : 1" size={56} />
      <Label x={960} y={640} start={s + d * 0.35 + 14} k="1 : 2" size={56} />
      <Label x={1440} y={640} start={tHalf + 8} v="no half atoms" size={50} />
      <PopSfx at={s + 24} />
      <PopSfx at={s + d * 0.35 + 14} />
    </>
  );
};

const ModelShot: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s2-9");
  return (
    <>
      <Svg>
        <g transform={`translate(960 450) scale(${0.9 + 0.1 * pop(f, s)})`}>
          <SolidSphere cx={0} cy={0} r={180} />
        </g>
      </Svg>
      <Title x={960} y={235} start={s + 4} text="Solid Sphere model" size={60} color={C.accent} />
      <Label x={960} y={770} start={s + 40} k="model" v="= a picture that explains" />
    </>
  );
};

const Prediction: React.FC = () => {
  const { at } = useAt();
  const s = at("s2-10");
  return (
    <>
      <Svg>
        <SolidSphere cx={640} cy={480} r={180} />
      </Svg>
      <InfoCard x={1260} y={480} w={600} h={300} start={s + 10} head="Prediction" text="Nothing inside">
        <svg width={600} height={120} viewBox="0 0 600 120" style={{ position: "absolute", left: 0, top: 88 }}>
          <circle cx={290} cy={55} r={36} fill="none" stroke={C.muted} strokeWidth={9} />
          <line x1={316} y1={81} x2={350} y2={112} stroke={C.muted} strokeWidth={12} strokeLinecap="round" />
        </svg>
      </InfoCard>
    </>
  );
};

export const Scene2: React.FC = () => (
  <Shots
    shots={[
      { from: "s2-1", el: <Laws /> },
      { from: "s2-2", el: <Lavoisier /> },
      { from: "s2-4", el: <Proust /> },
      { from: "s2-5", el: <Dalton /> },
      { from: "s2-6", el: <OneBall /> },
      { from: "s2-7", el: <Rows /> },
      { from: "s2-8", el: <Join /> },
      { from: "s2-9", el: <ModelShot /> },
      { from: "s2-10", el: <Prediction /> },
    ]}
  />
);
