import * as FileSystem from "expo-file-system";
import { BACKEND_URL } from "@/config";

function filenameFromUri(uri: string) {
  const base = uri.split("/").pop() || "upload.jpg";
  return base.includes(".") ? base : base + ".jpg";
}
async function normalizeToFileUri(uri: string) {
  if (uri.startsWith("file://")) return uri;
  const target = FileSystem.cacheDirectory + filenameFromUri(uri);
  await FileSystem.copyAsync({ from: uri, to: target });
  return target;
}

export async function sendImageForRedaction(fileUri: string): Promise<{ bytes: Uint8Array; applied: boolean }> {
  const normalized = await normalizeToFileUri(fileUri);

  const form = new FormData();
  // TS doesn’t know RN’s file descriptor shape. Cast once and move on.
  form.append("file", {
    uri: normalized,
    name: filenameFromUri(normalized),
    type: "image/jpeg"
  } as any);

  const res = await fetch(`${BACKEND_URL}/process`, {
    method: "POST",
    body: form,
    headers: { Accept: "application/octet-stream" }
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Backend error ${res.status}: ${text}`);
  }

  const appliedHeader = res.headers.get("x-redactions"); // "some" or "none"
  const applied = appliedHeader === "some";

  const arrayBuffer = await res.arrayBuffer();
  return { bytes: new Uint8Array(arrayBuffer), applied };
}
