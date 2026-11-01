import React, { useContext } from "react";
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from "remotion";
import { SceneCtx, ShotCtx } from "../timing";

export type Shot = { from: string; el: React.ReactNode };

const LEAD = 6; // a shot starts slightly before its line
const XFADE = 10; // cross-fade between shots

const Fade: React.FC<{ dur: number; first: boolean; last: boolean; children: React.ReactNode }> = ({
  dur,
  first,
  last,
  children,
}) => {
  const frame = useCurrentFrame();
  const a = first ? 1 : interpolate(frame, [0, XFADE], [0, 1], { extrapolateRight: "clamp" });
  const b = last ? 1 : interpolate(frame, [dur - XFADE, dur], [1, 0], { extrapolateLeft: "clamp" });
  return <AbsoluteFill style={{ opacity: Math.min(a, b) }}>{children}</AbsoluteFill>;
};

/**
 * One idea on screen at a time: each shot starts with its narration line and
 * cross-fades into the next shot. Shots whose line was cut are skipped.
 */
export const Shots: React.FC<{ shots: Shot[] }> = ({ shots }) => {
  const { lines, duration } = useContext(SceneCtx);
  const live = shots.filter((s) => lines[s.from]);
  const starts = live.map((s, i) => (i === 0 ? 0 : Math.max(0, lines[s.from].startFrame - LEAD)));
  return (
    <>
      {live.map((s, i) => {
        const from = starts[i];
        const isLast = i === live.length - 1;
        const to = isLast ? duration : starts[i + 1] + XFADE;
        const dur = Math.max(1, to - from);
        return (
          <Sequence key={s.from} from={from} durationInFrames={dur} layout="none">
            <ShotCtx.Provider value={{ offset: from }}>
              <Fade dur={dur} first={i === 0} last={isLast}>
                {s.el}
              </Fade>
            </ShotCtx.Provider>
          </Sequence>
        );
      })}
    </>
  );
};
