const configuredBaseUrl = (import.meta.env.VITE_BACKEND_API_URL || "").replace(/\/+$/, "");

export const backendBaseUrl = configuredBaseUrl || "";
export const isRemoteBackend = Boolean(configuredBaseUrl);

export function apiUrl(path) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${backendBaseUrl}${normalizedPath}`;
}

export function resolveBackendUrl(url) {
  if (!url) return "";
  if (/^https?:\/\//i.test(url) || url.startsWith("blob:")) return url;
  if (!configuredBaseUrl) return url;
  return `${configuredBaseUrl}${url.startsWith("/") ? url : `/${url}`}`;
}

export async function apiFetch(path, options = {}) {
  const response = await fetch(apiUrl(path), options);
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await response.json() : await response.text();

  if (!response.ok) {
    const message = typeof data === "object" ? data.message || data.error : data;
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return data;
}

function sendWithProgress({ method, url, body, headers = {}, onProgress }) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open(method, url);

    Object.entries(headers).forEach(([key, value]) => {
      if (value) xhr.setRequestHeader(key, value);
    });

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(Math.round((event.loaded / event.total) * 100));
    };

    xhr.onload = () => {
      let data = {};
      try {
        data = xhr.responseText ? JSON.parse(xhr.responseText) : {};
      } catch {
        data = xhr.responseText || {};
      }

      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(data);
        return;
      }

      const message = typeof data === "object" ? data.message || data.error : data;
      reject(new Error(message || `Upload failed with status ${xhr.status}`));
    };

    xhr.onerror = () => reject(new Error("Upload failed because the backend is not reachable."));
    xhr.send(body);
  });
}

export function uploadMatchVideo({ matchId, file, uploadUrl, onProgress }) {
  if (uploadUrl) {
    return sendWithProgress({
      method: "PUT",
      url: resolveBackendUrl(uploadUrl),
      body: file,
      headers: { "Content-Type": file.type || "application/octet-stream" },
      onProgress,
    });
  }

  const formData = new FormData();
  formData.append("file", file);

  return sendWithProgress({
    method: "POST",
    url: apiUrl(`/api/matches/${matchId}/upload`),
    body: formData,
    onProgress,
  });
}

export function openJobEventSource(streamUrl, jobId) {
  const sourceUrl = streamUrl ? resolveBackendUrl(streamUrl) : apiUrl(`/api/jobs/${jobId}/events`);
  return new EventSource(sourceUrl);
}

export function clipPlaybackUrl(clip) {
  if (clip.video_url) return resolveBackendUrl(clip.video_url);
  if (!clip.match_id || !clip.clip_id) return "";
  return apiUrl(`/api/matches/${clip.match_id}/clips/${clip.clip_id}`);
}

export function clipThumbnailUrl(clip) {
  return clip.thumbnail_url ? resolveBackendUrl(clip.thumbnail_url) : "";
}
