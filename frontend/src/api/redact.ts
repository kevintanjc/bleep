import * as FileSystem from "expo-file-system";
import { apiFetch } from "./client";

type RedactResult = { bytes: Uint8Array; applied: boolean };

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

export async function sendImageForRedaction(fileUri: string): Promise<RedactResult> {
  const normalized = await normalizeToFileUri(fileUri);
  const form = new FormData();
  form.append("file", {
    uri: normalized,
    name: filenameFromUri(normalized),
    type: "image/jpeg"
  } as any);

  const res = await apiFetch("/process", {
    method: "POST",
    headers: { Accept: "application/octet-stream" },
    body: form
  });

  const applied = res.headers.get("x-redactions") === "some";
  const buf = await res.arrayBuffer();
  return { bytes: new Uint8Array(buf), applied };
}
