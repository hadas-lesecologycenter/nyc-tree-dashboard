import React from "react";
import { useCurrentFrame } from "remotion";
import { C } from "../theme";
import { useAt } from "../timing";
import { Shots } from "../components/Shots";
import { Arrow, Label, Svg, Title } from "../components/ui";
import { pop, prog } from "../components/anim";
import { ModelIcon, MODELS } from "../components/models";

const X = (i: number) => 240 + i * 360;
const Y = 470;

const Row: React.FC<{ start: number; names?: boolean }> = ({ start, names = true }) => {
  const f = useCurrentFrame();
  return (
    <>
      <Svg>
        {MODELS.map((m, i) => (
          <g key={i} transform={`translate(${X(i)} ${Y}) scale(${pop(f, start + i * 6)}) translate(${-X(i)} ${-Y})`}>
            <ModelIcon i={i} cx={X(i)} cy={Y} r={95} frame={f} />
          </g>
        ))}
      </Svg>
      {names &&
        MODELS.map((m, i) => (
          <React.Fragment key={i}>
            <Title x={X(i)} y={605} start={start + i * 6 + 4} text={m.name} size={38} />
            <Title x={X(i)} y={650} start={start + i * 6 + 4} text={m.year} size={34} color={C.accent} />
          </React.Fragment>
        ))}
    </>
  );
};

const Five: React.FC = () => {
  const { at } = useAt();
  const s = at("s7-1");
  return (
    <>
      <Row start={s} />
      <Label x={960} y={260} start={s + 10} k="Five models" />
    </>
  );
};

const Evidence: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s = at("s7-1");
  const s2 = at("s7-2");
  const d = end("s7-2") - s2;
  const step = (i: number) => s2 + 4 + (d * i) / 5;
  const labels = ["two laws", "cathode ray tube", "gold foil", "emission spectra", "electron waves"];
  return (
    <>
      <Row start={-100} />
      <Svg>
        {/* two laws lead into Dalton */}
        <Arrow x1={X(0)} y1={300} x2={X(0)} y2={Y - 110} t={prog(f, step(0), 10)} color={C.accent} width={8} />
        {[1, 2, 3, 4].map((i) => (
          <Arrow key={i} x1={X(i - 1) + 105} y1={Y} x2={X(i) - 105} y2={Y} t={prog(f, step(i), 10)} color={C.accent} width={8} />
        ))}
      </Svg>
      <Label x={X(0)} y={255} start={step(0)} k={labels[0]} size={42} />
      {[1, 2, 3, 4].map((i) => (
        <Label key={i} x={(X(i - 1) + X(i)) / 2} y={i % 2 === 1 ? 735 : 255} start={step(i)} k={labels[i]} size={42} />
      ))}
    </>
  );
};

const LOOP = [
  { t: "Model", x: 960, y: 245 },
  { t: "Prediction", x: 1290, y: 420 },
  { t: "Experiment", x: 1160, y: 730 },
  { t: "Result", x: 760, y: 730 },
  { t: "New model", x: 630, y: 420 },
];

const Loop: React.FC = () => {
  const f = useCurrentFrame();
  const { at, end } = useAt();
  const s3 = at("s7-3");
  const s4 = at("s7-4");
  const d3 = end("s7-3") - s3;
  const d4 = end("s7-4") - s4;
  const starts = [s3 + 4, s3 + d3 * 0.3, s3 + d3 * 0.7, s4 + d4 * 0.25, s4 + d4 * 0.65];
  return (
    <>
      <Svg>
        {LOOP.map((p, i) => {
          const q = LOOP[(i + 1) % LOOP.length];
          const st = i < 4 ? starts[i + 1] - 8 : starts[4] + 25;
          const dx = q.x - p.x;
          const dy = q.y - p.y;
          const L = Math.hypot(dx, dy);
          const ux = dx / L;
          const uy = dy / L;
          const pad = 150;
          return (
            <Arrow key={i} x1={p.x + ux * pad} y1={p.y + uy * (pad * 0.55)} x2={q.x - ux * pad} y2={q.y - uy * (pad * 0.55)} t={prog(f, st, 10)} color={C.muted} width={8} />
          );
        })}
      </Svg>
      {LOOP.map((p, i) => (
        <Label key={i} x={p.x} y={p.y} start={starts[i]} k={i === 0 || i === 4 ? p.t : undefined} v={i === 0 || i === 4 ? undefined : p.t} size={50} />
      ))}
    </>
  );
};

const Calm: React.FC = () => {
  const { at } = useAt();
  const s = at("s7-5");
  return <Row start={s - 200} />;
};

const Final: React.FC = () => {
  const f = useCurrentFrame();
  const { at } = useAt();
  const s = at("s7-6");
  return (
    <>
      <div style={{ opacity: 1 - prog(f, s + 10, 20) * 0.65 }}>
        <Row start={-300} names={false} />
      </div>
      <Label x={960} y={680} start={s + 30} k="Science updates with evidence" size={64} />
    </>
  );
};

export const Scene7: React.FC = () => (
  <Shots
    shots={[
      { from: "s7-1", el: <Five /> },
      { from: "s7-2", el: <Evidence /> },
      { from: "s7-3", el: <Loop /> },
      { from: "s7-5", el: <Calm /> },
      { from: "s7-6", el: <Final /> },
    ]}
  />
);
