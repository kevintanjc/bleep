import React, { createContext, useContext, useMemo, useState, useCallback, ReactNode } from "react";

export type Original = {
  id: string;
  uri: string;
  createdAt: number;
  name?: string;
};

export type Redacted = {
  id: string;
  originalId: string;
  uri: string;
  applied: boolean;
  createdAt: number;
};

type GalleryState = {
  originals: Original[];
  redacted: Redacted[];
};

type GalleryAPI = {
  state: GalleryState;
  addOriginal: (orig: Original) => void;
  addRedacted: (red: Redacted) => void;
  getRedactedForOriginal: (originalId: string) => Redacted[];
};

const GalleryContext = createContext<GalleryAPI | null>(null);

export function useGallery() {
  const ctx = useContext(GalleryContext);
  if (!ctx) throw new Error("GalleryContext missing");
  return ctx;
}

export function GalleryProvider({ children }: { children: ReactNode }) {
  const [originals, setOriginals] = useState<Original[]>([]);
  const [redacted, setRedacted] = useState<Redacted[]>([]);

  const addOriginal = useCallback((orig: Original) => {
    setOriginals(prev => [orig, ...prev]);
  }, []);

  const addRedacted = useCallback((r: Redacted) => {
    setRedacted(prev => [r, ...prev]);
  }, []);

  const getRedactedForOriginal = useCallback(
    (originalId: string) => redacted.filter(r => r.originalId === originalId),
    [redacted]
  );

  const api = useMemo<GalleryAPI>(
    () => ({
      state: { originals, redacted },
      addOriginal,
      addRedacted,
      getRedactedForOriginal
    }),
    [originals, redacted, addOriginal, addRedacted, getRedactedForOriginal]
  );

  return <GalleryContext.Provider value={api}>{children}</GalleryContext.Provider>;
}
