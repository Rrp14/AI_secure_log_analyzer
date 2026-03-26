const API_BASE = '/api/proxy';

// ── Analyze ──────────────────────────────────────────────
// Backend signature: input_type: str = Form(...), content: str = Form(None), file: UploadFile = File(None), options: str = Form(None)
export async function analyzeLogs(inputType: 'text' | 'file', content: string | File) {
  const formData = new FormData();
  if (inputType === 'text') {
    formData.append('input_type', 'text');
    formData.append('content', content as string);
  } else {
    // Backend expects input_type="log" for file uploads (not "file")
    formData.append('input_type', 'log');
    formData.append('file', content as File);
  }
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const errBody = await res.json();
      detail = errBody.detail || errBody.message || JSON.stringify(errBody);
    } catch { /* ignore */ }
    throw new Error(`Analyze failed (${res.status}): ${detail}`);
  }
  return res.json();
}

// ── Response shape from /analyze (AnalyzeResponse):
// { summary, findings: [{type, value, line, risk}], risk_score, risk_level,
//   insights: string[], ai_analysis: {summary, risks, root_cause, attack_narrative},
//   anomalies, correlations, parsed_logs, action, masked_output }

// ── Incidents ────────────────────────────────────────────
// Backend: GET /incidents → { count: N, data: [...] }  (no limit/skip params)
export async function fetchIncidents() {
  const res = await fetch(`${API_BASE}/incidents`);
  if (!res.ok) throw new Error(`Fetch incidents failed: ${res.statusText}`);
  return res.json();
}

// Backend: GET /incidents/{ip} → { count: N, data: [...] }
export async function fetchIncidentsByIp(ip: string) {
  const res = await fetch(`${API_BASE}/incidents/${encodeURIComponent(ip)}`);
  if (!res.ok) throw new Error(`Fetch incidents by IP failed: ${res.statusText}`);
  return res.json();
}

// ── Logs ─────────────────────────────────────────────────
// Backend: GET /logs?skip=0&limit=20&ip=xxx → { logs: [{_id, ip, content, risk_level, created_at}], total: N }
export async function fetchLogs(limit = 20, skip = 0, ip?: string) {
  let url = `${API_BASE}/logs?limit=${limit}&skip=${skip}`;
  if (ip) url += `&ip=${encodeURIComponent(ip)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Fetch logs failed: ${res.statusText}`);
  return res.json();
}

// ── Producer ─────────────────────────────────────────────
export async function startProducer() {
  const res = await fetch(`${API_BASE}/producer/start`, { method: 'POST' });
  if (!res.ok) throw new Error(`Start producer failed: ${res.statusText}`);
  return res.json();
}

export async function stopProducer() {
  const res = await fetch(`${API_BASE}/producer/stop`, { method: 'POST' });
  if (!res.ok) throw new Error(`Stop producer failed: ${res.statusText}`);
  return res.json();
}

export async function getProducerStatus() {
  const res = await fetch(`${API_BASE}/producer/status`);
  if (!res.ok) throw new Error(`Get producer status failed: ${res.statusText}`);
  return res.json();
}

// ── WebSocket ────────────────────────────────────────────
export const WS_LIVE_LOGS_URL = 'wss://20.197.50.230:8000/ws/live_logs';
