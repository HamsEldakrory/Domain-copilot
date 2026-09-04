export function getApiBaseUrl() {
  const raw = (import.meta.env.VITE_API_BASE_URL || "/api").replace(/\/$/, "");
  if (raw.endsWith("/api")) {
    return raw;
  }
  return `${raw}/api`;
}
export function buildJobStreamUrl(jobId, accessToken) {
  const base = getApiBaseUrl();
  const token = encodeURIComponent(accessToken || "");
  return `${base}/jobs/${jobId}/stream/?access=${token}`;
}
