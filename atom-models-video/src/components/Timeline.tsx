import React from "react";
import { useCurrentFrame } from "remotion";
import { C, FONT } from "../theme";
import { ModelIcon, MODELS } from "./models";
import { pop, prog } from "./anim";
import { Svg } from "./ui";

export const NODE = (i: number) => ({ x: 240 + i * 360, y: 62, r: 40 });

export type TimelineState = { litAt: number[]; updatedAt: number[] };

/** Timeline bar at the top (1803 → 1926). Lights up the current model. */
export const Timeline: React.FC<{ state: TimelineState }> = ({ state }) => {
  const frame = useCurrentFrame();
  const pulse = 0.5 + 0.5 * Math.sin((frame / 30) * Math.PI); // one slow pulse every 2 s
  return (
    <>
      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 160, background: "rgba(10, 18, 31, 0.9)", borderBottom: `2px solid ${C.panelEdge}` }} />
      <Svg>
        <line x1={120} y1={62} x2={1790} y2={62} stroke={C.dim} strokeWidth={6} strokeLinecap="round" />
        <polygon points="1812,62 1786,48 1786,76" fill={C.dim} />
        {MODELS.map((m, i) => {
          const n = NODE(i);
          const lit = frame >= state.litAt[i];
          const upd = frame >= state.updatedAt[i];
          const current = lit && !upd;
          const s = lit ? pop(frame, Math.max(0, state.litAt[i])) : 0;
          return (
            <g key={i}>
              {current && <circle cx={n.x} cy={n.y} r={n.r + 10 + pulse * 5} fill="none" stroke={C.accent} strokeWidth={5} opacity={0.5 + 0.4 * pulse} />}
              <circle cx={n.x} cy={n.y} r={n.r} fill={lit ? "#0B1424" : C.bg2} stroke={current ? C.accent : lit ? C.muted : C.dim} strokeWidth={4} />
              {lit && (
                <g transform={`translate(${n.x} ${n.y}) scale(${Math.max(0.01, s)}) translate(${-n.x} ${-n.y})`} opacity={upd ? 0.75 : 1}>
                  <ModelIcon i={i} cx={n.x} cy={n.y} r={n.r - 8} frame={frame} />
                </g>
              )}
            </g>
          );
        })}
      </Svg>
      {MODELS.map((m, i) => {
        const n = NODE(i);
        const lit = frame >= state.litAt[i];
        const upd = frame >= state.updatedAt[i];
        const current = lit && !upd;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: n.x,
              top: 128,
              transform: "translate(-50%, -50%)",
              fontFamily: FONT,
              fontSize: 30,
              fontWeight: 700,
              whiteSpace: "nowrap",
              color: current ? C.accent : lit ? C.text : C.dim,
            }}
          >
            {m.year}
            {lit ? ` · ${m.name}` : ""}
          </div>
        );
      })}
      {MODELS.map((m, i) => {
        const n = NODE(i);
        if (frame < state.updatedAt[i]) return null;
        const t = prog(frame, state.updatedAt[i], 8);
        return (
          <div
            key={`u${i}`}
            style={{
              position: "absolute",
              left: n.x + 44,
              top: 30,
              transform: `translate(0, -50%) rotate(-8deg) scale(${0.6 + 0.4 * t})`,
              opacity: t,
              fontFamily: FONT,
              fontSize: 19,
              fontWeight: 700,
              letterSpacing: 1.5,
              color: C.updated,
              border: `2.5px solid ${C.updated}`,
              borderRadius: 6,
              padding: "1px 7px",
              background: "#0B1424",
            }}
          >
            UPDATED
          </div>
        );
      })}
    </>
  );
};
