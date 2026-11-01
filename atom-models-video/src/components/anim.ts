import { Easing, interpolate, spring } from "remotion";
import { FPS } from "../timing";

/** Gentle bounce-in, 0 → 1 (slight overshoot). */
export const pop = (frame: number, start: number) =>
  frame < start ? 0 : spring({ frame: frame - start, fps: FPS, config: { damping: 11, stiffness: 110, mass: 0.9 } });

/** Smooth 0 → 1 between two frames. */
export const prog = (frame: number, start: number, dur = 12) =>
  interpolate(frame, [start, start + dur], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Deterministic pseudo-random numbers. */
export const rand = (seed: number) => {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};
