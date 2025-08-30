import React, {
  createContext, useCallback, useContext, useEffect, useMemo, useRef, useState
} from "react";
import * as LocalAuthentication from "expo-local-authentication";
import * as SecureStore from "expo-secure-store";
import { PinModal } from "./PinModal";

export type AuthMethod = "biometric" | "pin";
export type AuthState = {
  isAuthenticated: boolean;
  method: AuthMethod | null;
  lastAuthAt: number | null;
};

type Ctx = {
  state: AuthState;
  authenticate: (opts?: { reason?: string }) => Promise<boolean>;
  lock: () => Promise<void>;
  setPin: (pin: string) => Promise<void>;
  hasPin: () => Promise<boolean>;
  signOut: () => Promise<void>;
};

const AuthContext = createContext<Ctx | null>(null);

const SS_KEYS = {
  pin: "auth_pin_v1",
  session: "auth_session_v1"
};

const SESSION_TTL_MS = 5 * 60 * 1000;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    isAuthenticated: false,
    method: null,
    lastAuthAt: null
  });

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // PIN modal plumbing
  const [pinVisible, setPinVisible] = useState(false);
  const pinResolverRef = useRef<((ok: boolean) => void) | null>(null);

  const startAutoLockTimer = useCallback(() => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setState(s => ({ ...s, isAuthenticated: false, method: null }));
      SecureStore.deleteItemAsync(SS_KEYS.session).catch(() => {});
    }, SESSION_TTL_MS);
  }, []);

  useEffect(() => {
    if (state.isAuthenticated) startAutoLockTimer();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [state.isAuthenticated, startAutoLockTimer]);

  useEffect(() => {
    const restore = async () => {
      try {
        const raw = await SecureStore.getItemAsync(SS_KEYS.session);
        if (!raw) return;
        const parsed = JSON.parse(raw) as AuthState;
        const fresh = parsed.lastAuthAt !== null && Date.now() - parsed.lastAuthAt < SESSION_TTL_MS;
        if (fresh) {
          setState({ isAuthenticated: true, method: parsed.method, lastAuthAt: parsed.lastAuthAt });
        }
      } catch {
        // ignore
      }
    };
    restore();
  }, []);

  const persistSession = useCallback(async (next: AuthState) => {
    try {
      await SecureStore.setItemAsync(SS_KEYS.session, JSON.stringify(next));
    } catch {
      // ignore
    }
  }, []);

  const hasHardware = useCallback(async () => {
    try {
      const compatible = await LocalAuthentication.hasHardwareAsync();
      const enrolled = await LocalAuthentication.isEnrolledAsync();
      return compatible && enrolled;
    } catch {
      return false;
    }
  }, []);

  const hasPin = useCallback(async () => {
    const v = await SecureStore.getItemAsync(SS_KEYS.pin);
    return !!v;
  }, []);

  const setPin = useCallback(async (pin: string) => {
    if (!/^[0-9]{4,8}$/.test(pin)) throw new Error("PIN must be 4 to 8 digits");
    await SecureStore.setItemAsync(SS_KEYS.pin, pin);
  }, []);

  const promptForPin = useCallback(async (): Promise<boolean> => {
    const saved = await SecureStore.getItemAsync(SS_KEYS.pin);
    if (!saved) return false;
    setPinVisible(true);
    return new Promise<boolean>(resolve => {
      pinResolverRef.current = resolve;
    });
  }, []);

  const finishPinPrompt = useCallback((ok: boolean) => {
    setPinVisible(false);
    if (pinResolverRef.current) {
      pinResolverRef.current(ok);
      pinResolverRef.current = null;
    }
  }, []);

  const authenticate = useCallback(async (opts?: { reason?: string }) => {
    let ok = false;
    let method: AuthMethod | null = null;

    if (await hasHardware()) {
      const res = await LocalAuthentication.authenticateAsync({
        promptMessage: opts?.reason || "Unlock Originals",
        disableDeviceFallback: false
      });
      ok = !!res.success;
      if (ok) method = "biometric";
    }

    if (!ok && await hasPin()) {
      ok = await promptForPin();
      if (ok) method = "pin";
    }

    if (ok) {
      const next: AuthState = { isAuthenticated: true, method, lastAuthAt: Date.now() };
      setState(next);
      await persistSession(next);
      startAutoLockTimer();
    }
    return ok;
  }, [hasHardware, hasPin, promptForPin, persistSession, startAutoLockTimer]);

  const lock = useCallback(async () => {
    setState({ isAuthenticated: false, method: null, lastAuthAt: null });
    await SecureStore.deleteItemAsync(SS_KEYS.session);
  }, []);

  const signOut = useCallback(async () => {
    await lock();
  }, [lock]);

  const ctx = useMemo<Ctx>(() => ({
    state, authenticate, lock, setPin, hasPin, signOut
  }), [state, authenticate, lock, setPin, hasPin, signOut]);

  return (
    <AuthContext.Provider value={ctx}>
      {children}
      <PinModal
        visible={pinVisible}
        onCancel={() => finishPinPrompt(false)}
        onSubmit={async pin => {
          const saved = await SecureStore.getItemAsync(SS_KEYS.pin);
          finishPinPrompt(Boolean(saved && pin === saved));
        }}
      />
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
};
