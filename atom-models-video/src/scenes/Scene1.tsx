import React from "react";
import { useCurrentFrame } from "remotion";
import { C } from "../theme";
import { useAt } from "../timing";
import { Shots } from "../components/Shots";
import { Arrow, Label, NameCard, PopSfx, Svg, Title } from "../components/ui";
import { lerp, pop, prog, rand } from "../components/anim";
import { SolidSphere } from "../components/models";

const Pencil: React.FC = () => {
  const f = useCurrentFrame();
  const z = prog(f, 8, 50);
  const s = lerp(1, 1.9, z);
  const tipX = 1530;
  const tx = lerp(0, 1250 - tipX, z);
  return (
    <>
      <Svg>
        <g transform={`translate(${tx} 0) translate(${tipX} 500) scale(${s}) translate(${-tipX} -500)`}>
          <rect x={240} y={445} width={1020} height={110} fill="#F2B632" />
          <rect x={240} y={445} width={1020} height={30} fill="#F7C95A" />
          <rect x={240} y={525} width={1020} height={30} fill="#D99A1F" />
          <rect x={180} y={445} width={70} height={110} rx={10} fill="#E58FA0" />
          <rect x={235} y={440} width={40} height={120} fill="#B8BEC8" />
          <polygon points="1260,445 1450,482 1450,518 1260,555" fill="#E9C9A0" />
          <polygon points="1450,482 1530,500 1450,518" fill="#3B3F46" />
        </g>
      </Svg>
      <Label x={1250} y={300} start={40} k="carbon" />
      {f > 46 && (
        <Svg>
          <Arrow x1={1250} y1={350} x2={1262} y2={470} t={prog(f, 46, 10)} color={C.accent} width={7} />
        </Svg>
      )}
    </>
  );
};

const Cut: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s1-2");
  const span = Math.max(130, end("s1-2") - s);
  const step = (span - 30) / 5;
  const cuts = [0, 1, 2, 3].map((k) => s + 8 + k * step);
  const reveal = s + 8 + 4 * step;
  let k = cuts.filter((c) => f >= c + 14).length; // number of finished cuts
  const w = 640 / Math.pow(2, k);
  const h = 320 / Math.pow(2, k);
  const cur = cuts[k];
  const sweep = cur !== undefined ? prog(f, cur, 12) : 0;
  const rv = prog(f, reveal, 16);
  const cx = 960;
  const cy = 500;
  return (
    <>
      <Svg>
        {/* pieces that were cut off slide away */}
        {cuts.map((c, i) => {
          if (f < c + 14) return null;
          const t = prog(f, c + 14, 16);
          const pw = 640 / Math.pow(2, i + 1);
          const ph = 320 / Math.pow(2, i);
          return (
            <rect key={i} x={cx - pw - t * 220} y={cy - ph / 2 + t * 40} width={pw} height={ph} rx={8} fill="#3B3F46" opacity={1 - t} />
          );
        })}
        <g opacity={1 - rv}>
          <rect x={cx - w / 2} y={cy - h / 2} width={w} height={h} rx={Math.min(12, w / 8)} fill="#3B3F46" stroke="#5A6170" strokeWidth={3} />
          {cur !== undefined && f >= cur && f < cur + 14 && (
            <line x1={cx} y1={cy - h / 2 - 40} x2={cx} y2={cy - h / 2 - 40 + (h + 80) * sweep} stroke="#FFFFFF" strokeWidth={6} strokeDasharray="14 10" />
          )}
        </g>
        {rv > 0 && (
          <g opacity={rv}>
            <circle cx={cx} cy={cy} r={lerp(30, 290, rv)} fill="#141F31" stroke={C.muted} strokeWidth={6} />
            {[-3, -2, -1, 0, 1, 2, 3].map((i) => (
              <g key={i} transform={`translate(${cx + i * 72} ${cy}) scale(${pop(f, reveal + 10 + (i + 3) * 3)})`}>
                <SolidSphere cx={0} cy={0} r={32} />
              </g>
            ))}
          </g>
        )}
      </Svg>
      <Label x={960} y={235} start={s + 4} v="smaller and smaller" end={reveal} size={48} />
      <Label x={1110} y={830} start={reveal + 30} k="atom" />
      {f > reveal + 34 && (
        <Svg>
          <Arrow x1={1110} y1={782} x2={1032} y2={545} t={prog(f, reveal + 34, 10)} color={C.accent} width={7} />
        </Svg>
      )}
      <PopSfx at={reveal + 10} />
    </>
  );
};

const Atomos: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s1-3");
  const mid = s + (end("s1-3") - s) * 0.55;
  return (
    <>
      <Svg>
        <g transform={`translate(960 410) scale(${pop(f, s)}) translate(-960 -410)`}>
          <SolidSphere cx={960} cy={410} r={130} />
          <line x1={960} y1={240} x2={960} y2={580} stroke="#FFFFFF" strokeWidth={7} strokeDasharray="18 14" />
        </g>
        {f > mid && (
          <g opacity={prog(f, mid, 8)}>
            <circle cx={1180} cy={300} r={52} fill={C.bg} stroke={C.updated} strokeWidth={8} />
            <line x1={1150} y1={270} x2={1210} y2={330} stroke={C.updated} strokeWidth={10} strokeLinecap="round" />
            <line x1={1210} y1={270} x2={1150} y2={330} stroke={C.updated} strokeWidth={10} strokeLinecap="round" />
          </g>
        )}
      </Svg>
      <Label x={960} y={705} start={s + 20} k="atomos" v="= can't be cut" size={70} />
    </>
  );
};

const Greeks: React.FC = () => {
  const { at, end } = useAt();
  const s = at("s1-4");
  const mid = s + (end("s1-4") - s) * 0.55;
  return (
    <>
      <NameCard x={560} y={470} start={s + 20} name="Leucippus" place="Ancient Greece" year="2,400 years ago" scale={0.85} />
      <NameCard x={1360} y={470} start={mid} name="Democritus" place="Ancient Greece" year="2,400 years ago" scale={0.85} />
      <Label x={1360} y={700} start={mid + 10} v="his student" size={44} />
    </>
  );
};

const Drift: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s1-5");
  const balls = Array.from({ length: 13 }, (_, i) => {
    const bx = 320 + rand(i + 3) * 1280;
    const by = 250 + rand(i + 40) * 430;
    const x = bx + Math.sin(f * 0.02 + i) * 40;
    const y = by + Math.cos(f * 0.017 + i * 1.3) * 30;
    return { x, y, r: 34 + rand(i + 9) * 10, i };
  });
  return (
    <>
      <Svg>
        {balls.map((b) => (
          <g key={b.i} transform={`translate(${b.x} ${b.y}) scale(${pop(f, s + b.i * 3)})`}>
            <SolidSphere cx={0} cy={0} r={b.r} />
          </g>
        ))}
      </Svg>
      <Label x={960} y={790} start={s + 30} k="atoms" v="+ empty space" />
    </>
  );
};

const Aristotle: React.FC = () => {
  const { at } = useAt();
  return <NameCard x={960} y={480} start={at("s1-6")} name="Aristotle" place="Ancient Greece" />;
};

const Elements: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s1-7");
  const d = end("s1-7") - s;
  const starts = [0.42, 0.58, 0.72, 0.86].map((p) => s + d * p - 6);
  const xs = [420, 780, 1140, 1500];
  const names = ["fire", "air", "earth", "water"];
  const icon = (i: number, x: number) => {
    const y = 450;
    if (i === 0)
      return (
        <g>
          <path d={`M${x} ${y - 120} C ${x + 90} ${y - 30}, ${x + 85} ${y + 90}, ${x} ${y + 95} C ${x - 85} ${y + 90}, ${x - 90} ${y - 10}, ${x - 30} ${y - 60} C ${x - 25} ${y - 20}, ${x - 10} ${y - 10}, ${x} ${y - 120} Z`} fill="#FF8A3D" />
          <path d={`M${x} ${y - 20} C ${x + 40} ${y + 20}, ${x + 40} ${y + 80}, ${x} ${y + 85} C ${x - 40} ${y + 80}, ${x - 40} ${y + 30}, ${x} ${y - 20} Z`} fill="#FFD166" />
        </g>
      );
    if (i === 1)
      return (
        <g fill="none" stroke="#CFE3FF" strokeWidth={12} strokeLinecap="round">
          <path d={`M${x - 100} ${y - 50} H ${x + 40} a 35 35 0 1 0 -35 -35`} />
          <path d={`M${x - 110} ${y + 10} H ${x + 70} a 30 30 0 1 1 -30 30`} />
          <path d={`M${x - 90} ${y + 70} H ${x + 10}`} />
        </g>
      );
    if (i === 2)
      return (
        <g>
          <path d={`M${x - 120} ${y + 90} Q ${x - 60} ${y - 70} ${x} ${y - 40} Q ${x + 70} ${y - 100} ${x + 120} ${y + 90} Z`} fill="#8B5E3C" />
          <circle cx={x - 30} cy={y + 40} r={16} fill="#A9805C" />
          <circle cx={x + 40} cy={y + 10} r={12} fill="#A9805C" />
        </g>
      );
    return <path d={`M${x} ${y - 120} C ${x + 40} ${y - 50}, ${x + 85} ${y + 10}, ${x + 85} ${y + 45} A 85 85 0 0 1 ${x - 85} ${y + 45} C ${x - 85} ${y + 10}, ${x - 40} ${y - 50}, ${x} ${y - 120} Z`} fill="#4FA8FF" />;
  };
  return (
    <>
      <Svg>
        {xs.map((x, i) => (
          <g key={i} transform={`translate(${x} 450) scale(${pop(f, starts[i])}) translate(${-x} -450)`}>
            {icon(i, x)}
          </g>
        ))}
      </Svg>
      {xs.map((x, i) => (
        <Label key={i} x={x} y={660} start={starts[i] + 4} v={names[i]} size={50} />
      ))}
    </>
  );
};

const Hourglass: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s1-8");
  const t = prog(f, s, 90);
  return (
    <>
      <Svg>
        <g transform={`translate(960 430) scale(${pop(f, s)}) translate(-960 -430)`}>
          <rect x={850} y={250} width={220} height={22} rx={8} fill="#8B5E3C" />
          <rect x={850} y={588} width={220} height={22} rx={8} fill="#8B5E3C" />
          <path d="M880 272 L1040 272 L975 430 L1040 588 L880 588 L945 430 Z" fill="rgba(200,225,255,0.12)" stroke="#CFE3FF" strokeWidth={5} />
          <path d={`M${900 + 40 * t} ${300 + 110 * t} L${1020 - 40 * t} ${300 + 110 * t} L966 425 L954 425 Z`} fill={C.accent} />
          <path d={`M${920 - 20 * t} 584 L${1000 + 20 * t} 584 L${960 + 8} ${584 - 90 * t} L${960 - 8} ${584 - 90 * t} Z`} fill={C.accent} />
          <rect x={957} y={428} width={6} height={150} fill={C.accent} opacity={t < 1 ? 0.8 : 0} />
        </g>
      </Svg>
      <Label x={960} y={735} start={s + 20} k="almost 2,000 years" />
    </>
  );
};

const Question: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s1-9");
  return (
    <>
      <Svg>
        <g transform={`translate(960 440) scale(${pop(f, s)}) translate(-960 -440)`}>
          <circle cx={960} cy={440} r={190} fill="rgba(143,163,191,0.12)" stroke={C.sphere} strokeWidth={8} strokeDasharray="26 18" />
        </g>
      </Svg>
      <Title x={960} y={440} start={s + 10} text="?" size={240} color={C.accent} />
      <Label x={960} y={735} start={s + 26} v="What's inside an atom?" />
    </>
  );
};

const Experiment: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s1-10");
  const bub = [0, 1, 2, 3, 4].map((i) => {
    const t = ((f + i * 17) % 70) / 70;
    return { x: 930 + ((i * 37) % 70), y: 560 - t * 170, o: 1 - t };
  });
  return (
    <>
      <Svg>
        <g transform={`translate(960 450) scale(${pop(f, s)}) translate(-960 -450)`}>
          <path d="M890 250 L890 380 L800 600 Q795 620 815 620 L1105 620 Q1125 620 1120 600 L1030 380 L1030 250 Z" fill="rgba(200,225,255,0.10)" stroke="#CFE3FF" strokeWidth={6} />
          <path d="M852 480 L1068 480 L1120 600 Q1125 620 1105 620 L815 620 Q795 620 800 600 Z" fill={C.good} opacity={0.75} />
          <rect x={870} y={238} width={180} height={18} rx={8} fill="#CFE3FF" />
          {bub.map((b, i) => (
            <circle key={i} cx={b.x} cy={b.y} r={9} fill="#FFFFFF" opacity={b.y > 480 ? 0.7 * b.o : 0} />
          ))}
        </g>
      </Svg>
      <Label x={960} y={740} start={s + 24} k="experiment" v="= a test" />
    </>
  );
};

export const Scene1: React.FC = () => (
  <Shots
    shots={[
      { from: "s1-1", el: <Pencil /> },
      { from: "s1-2", el: <Cut /> },
      { from: "s1-3", el: <Atomos /> },
      { from: "s1-4", el: <Greeks /> },
      { from: "s1-5", el: <Drift /> },
      { from: "s1-6", el: <Aristotle /> },
      { from: "s1-7", el: <Elements /> },
      { from: "s1-8", el: <Hourglass /> },
      { from: "s1-9", el: <Question /> },
      { from: "s1-10", el: <Experiment /> },
    ]}
  />
);
