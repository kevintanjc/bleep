import { BACKEND_URL } from "@/config";

export async function apiFetch(path: string, init?: RequestInit) {
  const res = await fetch(`${BACKEND_URL}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText} ${text ? "- " + text : ""}`);
  }
  return res;
}