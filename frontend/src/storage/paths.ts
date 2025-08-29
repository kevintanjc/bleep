import * as FileSystem from "expo-file-system";
import { ORIGINALS_DIR, REDACTED_DIR } from "@/config";
import { Buffer } from "buffer";

const originalsPath = FileSystem.documentDirectory + ORIGINALS_DIR + "/";
const redactedPath = FileSystem.documentDirectory + REDACTED_DIR + "/";

export async function ensureDirs() {
  await FileSystem.makeDirectoryAsync(originalsPath, { intermediates: true }).catch(() => {});
  await FileSystem.makeDirectoryAsync(redactedPath, { intermediates: true }).catch(() => {});
}

export function getOriginalsPath() { return originalsPath; }
export function getRedactedPath() { return redactedPath; }

export async function saveToOriginals(localUri: string) {
  const filename = localUri.split("/").pop() || `img_${Date.now()}.jpg`;
  const dest = originalsPath + filename;
  await FileSystem.copyAsync({ from: localUri, to: dest });
  return dest;
}

export async function saveToRedactedFromUri(srcUri: string, name: string) {
  const dest = `${redactedDir()}/${name}`;
  await FileSystem.copyAsync({ from: srcUri, to: dest });
  return dest;
}

export function redactedDir() {
  return FileSystem.documentDirectory + "redacted";
}

export async function listImages(dir: "originals" | "redacted") {
  const base = dir === "originals" ? originalsPath : redactedPath;
  const files = await FileSystem.readDirectoryAsync(base);
  return files.filter(f => f.match(/\.(jpg|jpeg|png|heic)$/i)).map(f => base + f).sort((a, b) => b.localeCompare(a));
}

export async function clearAll() {
  await FileSystem.deleteAsync(originalsPath, { idempotent: true });
  await FileSystem.deleteAsync(redactedPath, { idempotent: true });
  await ensureDirs();
}