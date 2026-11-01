import React from "react";
import { C } from "../theme";

/** A two-pan balance. tilt in degrees (positive = left side down). */
export const Balance: React.FC<{
  cx: number;
  tilt: number;
  left: (x: number, y: number) => React.ReactNode;
  right: (x: number, y: number) => React.ReactNode;
}> = ({ cx, tilt, left, right }) => {
  const py = 360;
  const half = 270;
  const a = (tilt * Math.PI) / 180;
  const lx = cx - half * Math.cos(a);
  const ly = py + half * Math.sin(a);
  const rx = cx + half * Math.cos(a);
  const ry = py - half * Math.sin(a);
  const drop = 170;
  const pan = (x: number, y: number) => (
    <g>
      <line x1={x} y1={y} x2={x - 90} y2={y + drop} stroke={C.muted} strokeWidth={4} />
      <line x1={x} y1={y} x2={x + 90} y2={y + drop} stroke={C.muted} strokeWidth={4} />
      <path d={`M${x - 120} ${y + drop} Q ${x} ${y + drop + 50} ${x + 120} ${y + drop} Z`} fill="#6E7F99" />
    </g>
  );
  return (
    <g>
      <polygon points={`${cx - 110},720 ${cx + 110},720 ${cx + 30},690 ${cx - 30},690`} fill="#6E7F99" />
      <rect x={cx - 14} y={py} width={28} height={335} fill="#6E7F99" />
      <line x1={lx} y1={ly} x2={rx} y2={ry} stroke="#B8C4D6" strokeWidth={16} strokeLinecap="round" />
      <circle cx={cx} cy={py} r={18} fill={C.accent} />
      {pan(lx, ly)}
      {pan(rx, ry)}
      {left(lx, ly + drop)}
      {right(rx, ry + drop)}
    </g>
  );
};

