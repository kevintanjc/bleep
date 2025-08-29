import * as FileSystem from "expo-file-system";

export async function saveBytesToCache(bytes: Uint8Array, name: string) {
  const path = FileSystem.cacheDirectory + name;
  // Convert to base64 for writeAsStringAsync
  let b64 = "";
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    b64 += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk) as unknown as number[]);
  }
  const base64 = global.btoa ? global.btoa(b64) : Buffer.from(bytes).toString("base64");
  await FileSystem.writeAsStringAsync(path, base64, { encoding: FileSystem.EncodingType.Base64 });
  return "file://" + path.replace(/^file:\/\//, "");
}
