import React, { createContext, useCallback, useContext, useMemo, useState } from "react";

type Img = { uri: string };
type InspectorState = { visible: boolean; items: Img[]; index: number };

type Ctx = {
  state: InspectorState;
  open: (items: Img[], index: number) => void;
  close: () => void;
};

const InspectorContext = createContext<Ctx | null>(null);

export const InspectorProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<InspectorState>({ visible: false, items: [], index: 0 });

  const open = useCallback((items: Img[], index: number) => {
    setState({ visible: true, items, index });
  }, []);

  const close = useCallback(() => setState(s => ({ ...s, visible: false })), []);

  const value = useMemo(() => ({ state, open, close }), [state, open, close]);

  return (
    <InspectorContext.Provider value={value}>
      {children}
    </InspectorContext.Provider>
  );
};

export const useInspector = () => {
  const ctx = useContext(InspectorContext);
  if (!ctx) throw new Error("useInspector must be used within InspectorProvider");
  return ctx;
};