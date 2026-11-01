import React from "react";
import { AbsoluteFill, Audio, Sequence, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, FONT } from "./theme";
import { PartT, SceneProvider, TIMING, absLine } from "./timing";
import { Timeline, TimelineState } from "./components/Timeline";
import { Captions, buildCaptions } from "./components/Captions";
import { UPD } from "./components/Update";
import { pop } from "./components/anim";
import { Scene1 } from "./scenes/Scene1";
import { Scene2 } from "./scenes/Scene2";
import { Scene3 } from "./scenes/Scene3";
import { Scene4 } from "./scenes/Scene4";
import { Scene5 } from "./scenes/Scene5";
import { Scene6 } from "./scenes/Scene6";
import { Scene7 } from "./scenes/Scene7";

const SCENES: Record<string, React.FC> = {
  s1: Scene1,
  s2: Scene2,
  s3: Scene3,
  s4: Scene4,
  s5: Scene5,
  s6: Scene6,
  s7: Scene7,
};

const NEVER = 1e9;

const timelineState = (partId: string, part: PartT): TimelineState => {
  const L = (id: string) => absLine(part, id) ?? NEVER;
  const arrive = (id: string) => L(id) + UPD.flyStart + UPD.flyDur;
  const next = (id: string) => L(id) + UPD.next;
  if (partId === "part1") {
    return {
      litAt: [L("s2-5"), next("s3-19") - UPD.next, NEVER, NEVER, NEVER],
      updatedAt: [arrive("s3-16"), NEVER, NEVER, NEVER, NEVER],
    };
  }
  return {
    litAt: [-1, -1, next("s4-21"), next("s5-17"), next("s6-10")],
    updatedAt: [-1, arrive("s4-21"), arrive("s5-17"), arrive("s6-10"), NEVER],
  };
};

const SceneFade: React.FC<{ dur: number; children: React.ReactNode }> = ({ dur, children }) => {
  const frame = useCurrentFrame();
  const o = Math.min(
    interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" }),
    interpolate(frame, [dur - 12, dur], [1, 0], { extrapolateLeft: "clamp" }),
  );
  return <AbsoluteFill style={{ opacity: o }}>{children}</AbsoluteFill>;
};

const TitleCard: React.FC<{ partNo: number; dur: number }> = ({ partNo, dur }) => {
  const frame = useCurrentFrame();
  const s = pop(frame, 4);
  const o = interpolate(frame, [dur - 12, dur], [1, 0], { extrapolateLeft: "clamp" });
  return (
    <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", opacity: o, fontFamily: FONT, color: C.text }}>
      <div style={{ transform: `scale(${0.85 + 0.15 * s})`, opacity: Math.min(1, s * 1.4), textAlign: "center" }}>
        <div style={{ fontSize: 110, fontWeight: 700 }}>Models of the Atom</div>
        <div style={{ fontSize: 70, fontWeight: 700, color: C.accent, marginTop: 20 }}>Part {partNo}</div>
      </div>
    </AbsoluteFill>
  );
};

export const Part: React.FC<{ partId: string }> = ({ partId }) => {
  const part = TIMING.parts[partId];
  const caps = buildCaptions(part);
  const state = timelineState(partId, part);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 55%, ${C.bg2} 0%, ${C.bg} 70%)` }}>
      <Sequence from={0} durationInFrames={part.titleFrames} layout="none">
        <TitleCard partNo={partId === "part1" ? 1 : 2} dur={part.titleFrames} />
      </Sequence>
      {part.scenes.map((s) => {
        const Comp = SCENES[s.id];
        return (
          <Sequence key={s.id} from={s.startFrame} durationInFrames={s.durationFrames} layout="none">
            <SceneProvider scene={s}>
              <Audio src={staticFile(s.audio)} />
              <SceneFade dur={s.durationFrames}>
                <Comp />
              </SceneFade>
            </SceneProvider>
          </Sequence>
        );
      })}
      <Sequence from={part.titleFrames - 10} layout="none">
        <Timeline state={state} />
      </Sequence>
      <Captions caps={caps} />
    </AbsoluteFill>
  );
};
