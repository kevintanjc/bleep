import { BACKEND_URL } from "@/config";

export async function apiFetch(path: string, init?: RequestInit) {
  console.log("apiFetch", BACKEND_URL + path, init?.method ?? "GET");
  const res = await fetch(`${BACKEND_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    console.log("apiFetch error", res.status, res.statusText, text);
    throw new Error(`HTTP ${res.status} ${res.statusText} ${text ? "- " + text : ""}`);
  }
  return res;
}