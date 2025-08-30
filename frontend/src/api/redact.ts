import * as FileSystem from "expo-file-system";
import { apiFetch } from "./client";
import { fromByteArray } from "base64-js";


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

export async function sendImageForRedaction(fileUri: string) {
  const normalized = await normalizeToFileUri(fileUri);
  
  const form = new FormData();
  form.append("file", {
    uri: normalized,
    name: filenameFromUri(normalized),
    type: "image/jpeg",
  } as any);

  const res = await apiFetch("/process", {
    method: "POST",
    headers: { Accept: "image/jpeg" },
    body: form,
  });

  const applied = res.headers.get("x-redactions") === "some";
  const buf = await res.arrayBuffer();
  const base64 = fromByteArray(new Uint8Array(buf));

  // unique filename to avoid cache collisions
  const fname = `redacted_${Date.now()}.jpg`;
  const filePath = FileSystem.cacheDirectory + fname;

  await FileSystem.writeAsStringAsync(filePath, base64, {
    encoding: FileSystem.EncodingType.Base64,
  });

  const displayUri = filePath; // keep file://
  const uri = `${displayUri}?t=${Date.now()}`;

  return { uri: uri, applied };
}