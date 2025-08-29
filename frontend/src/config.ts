import { Platform } from "react-native";
import 'dotenv/config';

export const ORIGINALS_DIR = "originals";
export const REDACTED_DIR = "redacted";
export const COMPUTER_LAN = process.env.COMPUTER_LAN;

// Android emulator address
export const EMULATOR = process.env.EMULATOR_LAN;

export const BACKEND_URL =
  Platform.OS === "android"
    ? __DEV__ ? EMULATOR : COMPUTER_LAN
    : COMPUTER_LAN;