import React from "react";
import { Composition } from "remotion";
import { Part } from "./Part";
import { TIMING, FPS } from "./timing";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Part1"
      component={Part}
      defaultProps={{ partId: "part1" }}
      durationInFrames={TIMING.parts.part1.totalFrames}
      fps={FPS}
      width={1920}
      height={1080}
    />
    <Composition
      id="Part2"
      component={Part}
      defaultProps={{ partId: "part2" }}
      durationInFrames={TIMING.parts.part2.totalFrames}
      fps={FPS}
      width={1920}
      height={1080}
    />
  </>
);
