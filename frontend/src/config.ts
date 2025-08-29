import Constants from "expo-constants";

type Extra = {
  BACKEND_URL: string;
};

const extra = (Constants.expoConfig?.extra ?? {}) as Partial<Extra>;
export const BACKEND_URL = extra.BACKEND_URL;

export const ORIGINALS_DIR = "originals";
export const REDACTED_DIR = "redacted";
export const COMPUTER_LAN = process.env.COMPUTER_LAN;

// Android emulator address
export const EMULATOR = process.env.EMULATOR_LAN;