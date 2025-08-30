import "dotenv/config";
import { ExpoConfig, ConfigContext } from "expo/config";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: "bleep",
  slug: "bleep",
  version: "1.0.0",
  plugins: [
    "expo-secure-store",
    "expo-local-authentication"
  ],
  extra: {
    BACKEND_URL: process.env.BACKEND_URL
  }
});