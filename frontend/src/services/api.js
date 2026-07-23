const BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";
const PROXY_BASE = ""; // Handled by Vite proxy in dev

/** Helper to handle JSON responses and HTTP errors */
async function fetchApi(endpoint, options = {}) {
  const url = endpoint.startsWith("/chat") || endpoint.startsWith("/static") 
    ? endpoint 
    : `${PROXY_BASE}${endpoint}`;

  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || `API Error: ${res.status}`);
  }

  return res.json();
}

export async function rephraseText(text, mode = "standard") {
  return fetchApi("/api/rephrase", {
    method: "POST",
    body: JSON.stringify({ text, mode }),
  });
}

export async function translateText(text, language) {
  return fetchApi("/api/translate", {
    method: "POST",
    body: JSON.stringify({ text, language }),
  });
}

export async function sendChatMessage(text, session_id = null) {
  return fetchApi("/chat", {
    method: "POST",
    body: JSON.stringify({ text, session_id }),
  });
}

export async function textToSpeech(text, language) {
  return fetchApi("/api/tts", {
    method: "POST",
    body: JSON.stringify({ text, language }),
  });
}

export async function checkGrammar(text) {
  return fetchApi("/api/grammar", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export async function registerUser(name, email, password) {
  return fetchApi("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password }),
  });
}

export async function loginUser(email, password) {
  return fetchApi("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export async function getProfile(token) {
  return fetchApi("/api/user/profile", {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function updateProfile(token, data) {
  return fetchApi("/api/user/profile", {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(data),
  });
}

// ── History & Stats ──────────────────────────────────────────────────────────

export async function getHistory(token, params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchApi(`/api/history${query ? `?${query}` : ""}`, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function deleteHistoryItem(token, id) {
  return fetchApi(`/api/history/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function getStats(token) {
  return fetchApi("/api/stats", {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export async function savePreferences(token, prefs) {
  return fetchApi("/api/user/preferences", {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(prefs),
  });
}

// ── Batch Processing ──────────────────────────────────────────────────────────

export async function batchRephrase(texts) {
  return fetchApi("/api/batch/rephrase", {
    method: "POST",
    body: JSON.stringify({ texts }),
  });
}

export async function batchTranslate(texts, language) {
  return fetchApi("/api/batch/translate", {
    method: "POST",
    body: JSON.stringify({ texts, language }),
  });
}

export async function getBatchStatus(jobId) {
  return fetchApi(`/api/batch/status/${jobId}`);
}

// ── OCR Pipeline ──────────────────────────────────────────────────────────────

export async function getOcrLanguages() {
  return fetchApi("/api/ocr/languages");
}

export async function processOcr(formData) {
  // FormData requests should NOT have Content-Type header manually set, browser handles boundary
  const res = await fetch(`${PROXY_BASE}/api/ocr`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export async function ocrRephrase(formData) {
  const res = await fetch(`${PROXY_BASE}/api/ocr-rephrase`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export async function ocrTranslate(formData) {
  const res = await fetch(`${PROXY_BASE}/api/ocr-translate`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

// ── Async Document Processing ────────────────────────────────────────────────

export async function extractPdfChunks(formData) {
  const res = await fetch(`${PROXY_BASE}/api/pdf/extract`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export async function asyncRephrase(text) {
  return fetchApi("/api/async/rephrase", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export async function asyncTranslate(text, language) {
  return fetchApi("/api/async/translate", {
    method: "POST",
    body: JSON.stringify({ text, language }),
  });
}

export async function asyncPdfRephrase(formData) {
  const res = await fetch(`${PROXY_BASE}/api/async/pdf/rephrase`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export async function asyncPdfTranslate(formData) {
  const res = await fetch(`${PROXY_BASE}/api/async/pdf/translate`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`API Error: ${res.status}`);
  return res.json();
}

export async function getAsyncStatus(jobId) {
  return fetchApi(`/api/async/status/${jobId}`);
}
