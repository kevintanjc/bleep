import { Platform } from "react-native";
import * as FileSystem from "expo-file-system";
import { BACKEND_URL } from "@/config";

function filenameFromUri(uri: string) {
  const base = uri.split("/").pop() || "upload.jpg";
  return base.includes(".") ? base : base + ".jpg";
}

async function normalizeToFileUri(uri: string) {
  if (uri.startsWith("file://")) return uri;

  // Handle content:// and other schemes, Android special
  const target = FileSystem.cacheDirectory + filenameFromUri(uri);
  await FileSystem.copyAsync({ from: uri, to: target });
  return target;
}

export async function sendImageForRedaction(fileUri: string) {
  // 1) Normalize URI so FormData can read the file
  const normalized = await normalizeToFileUri(fileUri);

  // 2) Build FormData without manually setting Content-Type
  const form = new FormData();
  form.append("file", {
    // @ts-ignore RN FormData
    uri: normalized,
    name: filenameFromUri(normalized),
    type: "image/jpeg"
  } as any);

  // 3) Point to a reachable backend host
  // Use your LAN IP for devices, or 10.0.2.2 on Android emulator
  const url = `${BACKEND_URL}/process`;

  const res = await fetch(url, {
    method: "POST",
    body: form,
    headers: { Accept: "application/octet-stream" }
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error ${res.status}: ${text}`);
  }

  // 4) Robust binary extraction path
  // Some RN builds struggle with res.blob(). arrayBuffer() is safer.
  const arrayBuffer = await res.arrayBuffer();
  return new Uint8Array(arrayBuffer);
}
