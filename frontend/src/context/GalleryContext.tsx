import {
  createContext,
  useContext,
  useMemo,
  useState,
  PropsWithChildren
} from "react";

type GalleryCtx = {
  originals: string[];
  redacted: string[];
  addOriginal: (uri: string) => void;
  addRedacted: (uri: string) => void;
  reset: () => void;
};

const Ctx = createContext<GalleryCtx | null>(null);

export function GalleryProvider({ children }: PropsWithChildren) {
  const [originals, setOriginals] = useState<string[]>([]);
  const [redacted, setRedacted] = useState<string[]>([]);

  const value = useMemo<GalleryCtx>(
    () => ({
      originals,
      redacted,
      addOriginal: u => setOriginals(x => [u, ...x]),
      addRedacted: u => setRedacted(x => [u, ...x]),
      reset: () => {
        setOriginals([]);
        setRedacted([]);
      }
    }),
    [originals, redacted]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useGallery() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useGallery must be used within GalleryProvider");
  return ctx;
}
