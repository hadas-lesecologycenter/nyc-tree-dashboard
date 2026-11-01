import React from "react";
import { useCurrentFrame } from "remotion";
import { C } from "../theme";
import { lerp, pop, prog } from "./anim";
import { ModelIcon } from "./models";
import { NODE } from "./Timeline";
import { Label, Stamp, Svg } from "./ui";

/** Frames after the line start: stamp, fly to the timeline, new model appears. */
export const UPD = { stamp: 8, flyStart: 32, flyDur: 26, next: 60 };

/**
 * THE MODEL gets stamped "UPDATED" and slides onto its timeline slot.
 * Then the NEW MODEL pops in with its name.
 */
export const UpdateShot: React.FC<{
  start: number; // line start, relative to the shot
  oldIndex: number; // model being replaced (slot on the timeline)
  newIndex?: number; // new model to show afterwards
  newName?: string;
  r?: number;
}> = ({ start, oldIndex, newIndex, newName, r = 190 }) => {
  const frame = useCurrentFrame();
  const cx = 960;
  const cy = 500;
  const t = prog(frame, start + UPD.flyStart, UPD.flyDur);
  const n = NODE(oldIndex);
  const x = lerp(cx, n.x, t);
  const y = lerp(cy, n.y, t);
  const sc = lerp(1, (n.r - 8) / r, t);
  const stampOpacity = 1 - prog(frame, start + UPD.flyStart, 8);
  const newStart = start + UPD.next;
  const ns = pop(frame, newStart);
  return (
    <>
      <Svg>
        {t < 1 && (
          <g transform={`translate(${x} ${y}) scale(${sc}) translate(${-cx} ${-cy})`}>
            <ModelIcon i={oldIndex} cx={cx} cy={cy} r={r} frame={frame} />
          </g>
        )}
        {newIndex !== undefined && ns > 0.001 && (
          <g transform={`translate(${cx} ${cy}) scale(${ns}) translate(${-cx} ${-cy})`}>
            <ModelIcon i={newIndex} cx={cx} cy={cy} r={r * 1.15} frame={frame} />
          </g>
        )}
      </Svg>
      {stampOpacity > 0 && (
        <div style={{ opacity: stampOpacity }}>
          <Stamp x={cx} y={cy} start={start + UPD.stamp} size={80} />
        </div>
      )}
      {newName && <Label x={960} y={790} start={newStart + 6} k={newName} />}
      {/* thin highlight ring behind the new model */}
      {newIndex !== undefined && ns > 0.001 && (
        <Svg>
          <circle cx={cx} cy={cy} r={r * 1.32} fill="none" stroke={C.accent} strokeOpacity={0.25 * Math.min(1, ns)} strokeWidth={4} />
        </Svg>
      )}
    </>
  );
};
