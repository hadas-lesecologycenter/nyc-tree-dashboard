import React, { createContext, useContext } from "react";
import raw from "./timing.json";

export type LineT = {
  id: string;
  text: string;
  start: number;
  end: number;
  startFrame: number;
  endFrame: number;
  silent?: boolean;
  cut?: boolean;
};

export type SceneT = {
  id: string;
  title: string;
  audio: string;
  startFrame: number;
  durationFrames: number;
  lines: LineT[];
};

export type PartT = {
  title: string;
  titleFrames: number;
  totalFrames: number;
  scenes: SceneT[];
};

export const TIMING = raw as unknown as { fps: number; parts: Record<string, PartT> };
export const FPS = TIMING.fps;

/** Absolute frame (inside a part) at which a line starts. Null if the line was cut. */
export const absLine = (part: PartT, id: string): number | null => {
  for (const s of part.scenes) {
    const l = s.lines.find((x) => x.id === id);
    if (l) return s.startFrame + l.startFrame;
  }
  return null;
};

type SceneCtxT = { lines: Record<string, LineT>; duration: number };
export const SceneCtx = createContext<SceneCtxT>({ lines: {}, duration: 0 });
export const ShotCtx = createContext<{ offset: number }>({ offset: 0 });

export const SceneProvider: React.FC<{ scene: SceneT; children: React.ReactNode }> = ({ scene, children }) => {
  const lines: Record<string, LineT> = {};
  scene.lines.forEach((l) => (lines[l.id] = l));
  return React.createElement(SceneCtx.Provider, { value: { lines, duration: scene.durationFrames } }, children);
};

/**
 * Returns a function that gives the frame (relative to the current shot) at which a line starts.
 * Lines that were cut return a very large number so their animations never start.
 */
export const useAt = () => {
  const { lines } = useContext(SceneCtx);
  const { offset } = useContext(ShotCtx);
  const at = (id: string) => (lines[id] ? lines[id].startFrame - offset : 1e9);
  const end = (id: string) => (lines[id] ? lines[id].endFrame - offset : 1e9);
  const has = (id: string) => Boolean(lines[id]);
  return { at, end, has };
};
