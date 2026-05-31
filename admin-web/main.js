const $ = (id) => document.getElementById(id);

const apiBaseEl = $("apiBase");
const serverIdEl = $("serverId");
const sessionSelectEl = $("sessionSelect");
const recentSelectEl = $("recentSelect");
const sessionIdManualEl = $("sessionIdManual");
const topicEl = $("topic");
const limitEl = $("limit");
const outEl = $("out");
const statusEl = $("status");
const authInfoEl = $("authInfo");

let timer = null;

function setStatus(s) {
  statusEl.textContent = s;
}
function setOut(s) {
  outEl.textContent = s;
}

function getSessionId() {
  const fromSelect = (sessionSelectEl.value || "").trim();
  if (fromSelect) return fromSelect;
  return (sessionIdManualEl.value || "").trim();
}

function apiUrl(path, params = {}) {
  const base = (apiBaseEl.value || "/api").replace(/\/+$/, "");
  const u = new URL(base + "/" + path.replace(/^\/+/, ""), location.origin);
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    u.searchParams.set(k, String(v));
  });
  return u.toString();
}

function fmtLog(it) {
  const ts = it.timestamp || "";
  const topic = it.topic ? ` [${it.topic}]` : "";
  const exit = (it.exit_code === 0 || it.exit_code) ? ` (exit=${it.exit_code})` : "";
  const cmd = it.command ? ` ${it.command}` : "";
  const head = `[${ts}]${topic}${exit}${cmd}`.trim();
  const body = (it.log || "").trim();
  return `${head}\n${body}\n`;
}

async function fetchJson(url, opts = {}) {
  const res = await fetch(url, { ...opts, headers: { "Accept": "application/json", ...(opts.headers || {}) } });
  const txt = await res.text();
  try {
    return JSON.parse(txt);
  } catch {
    throw new Error(`Non-JSON response (${res.status}): ${txt.slice(0, 400)}`);
  }
}

async function loadAuth() {
  try {
    const data = await fetchJson("/.auth/me");
    authInfoEl.textContent = JSON.stringify(data, null, 2);
  } catch {
    authInfoEl.textContent = "(no auth info)";
  }
}

async function health() {
  setStatus("health...");
  const data = await fetchJson(apiUrl("health"));
  setOut(JSON.stringify(data, null, 2));
  setStatus("health: ok");
}

async function loadSessions() {
  const server_id = serverIdEl.value.trim();
  if (!server_id) return alert("server_id required");
  localStorage.setItem("chronicle.server_id", server_id);
  setStatus("sessions...");
  const data = await fetchJson(apiUrl("sessions"));
  sessionSelectEl.innerHTML = "";
  (data.items || []).forEach((it) => {
    const sid = it.session_id || it.id || "";
    if (!sid) return;
    const opt = document.createElement("option");
    opt.value = sid;
    opt.textContent = sid;
    sessionSelectEl.appendChild(opt);
  });
  setStatus(`sessions: ${(data.items || []).length}`);
  setOut(JSON.stringify(data, null, 2));
}

async function loadRecentLogs() {
  const limit = parseInt(limitEl.value || "50", 10) || 50;
  const topic = topicEl.value.trim();
  setStatus("recent logs...");
  const data = await fetchJson(apiUrl("logs/recent", { limit, topic: topic || undefined }));
  const items = data.items || [];

  // unique server/session pairs
  const seen = new Set();
  const pairs = [];
  for (const it of items) {
    const server_id = (it.server_id || "").trim();
    const session_id = (it.session_id || "").trim();
    if (!server_id || !session_id) continue;
    const key = server_id + "::" + session_id;
    if (seen.has(key)) continue;
    seen.add(key);
    pairs.push({ server_id, session_id });
  }

  recentSelectEl.innerHTML = "";
  for (const p of pairs) {
    const opt = document.createElement("option");
    opt.value = p.server_id + "::" + p.session_id;
    opt.textContent = p.server_id + " / " + p.session_id;
    recentSelectEl.appendChild(opt);
  }

  // show raw items in output (for debugging)
  setOut(items.map(fmtLog).join("
"));
  setStatus("recent logs: " + items.length);
}

async function sessionGet() {
  const server_id = serverIdEl.value.trim();
  const session_id = getSessionId();
  if (!server_id || !session_id) return;
  setStatus("session/get...");
  const data = await fetchJson(apiUrl("session/get", { server_id, session_id }));
  setOut(JSON.stringify(data, null, 2));
  setStatus("session/get: ok");
}

async function loadLogsOnce() {
  const server_id = serverIdEl.value.trim();
  const session_id = getSessionId();
  if (!server_id || !session_id) return;
  const topic = topicEl.value.trim();
  const limit = parseInt(limitEl.value || "50", 10) || 50;
  setStatus("logs...");
  const data = await fetchJson(apiUrl("logs", { server_id, session_id, limit, topic: topic || undefined }));
  const items = data.items || [];
  setOut(items.map(fmtLog).join("\n"));
  setStatus(`logs: ${items.length}`);
}

function follow() {
  if (timer) return;
  timer = setInterval(loadLogsOnce, 5000);
  loadLogsOnce();
}

function stopFollow() {
  if (timer) clearInterval(timer);
  timer = null;
  setStatus("stopped");
}

// Auth buttons (SWA)
$("btnLogin").addEventListener("click", () => {
  location.href = "/.auth/login/aad";
});
$("btnLogout").addEventListener("click", () => {
  location.href = "/.auth/logout";
});

$("btnSessions").addEventListener("click", loadSessions);
$("btnHealth").addEventListener("click", health);
$("btnSessionGet").addEventListener("click", sessionGet);
$("btnStatus").addEventListener("click", async () => {
  await sessionGet();
  await loadLogsOnce();
});
$("btnLogs").addEventListener("click", loadLogsOnce);
$("btnFollow").addEventListener("click", follow);
$("btnStop").addEventListener("click", stopFollow);

// init
recentSelectEl.addEventListener("change", () => {
  const v = (recentSelectEl.value || "").trim();
  if (!v) return;
  const [server_id, session_id] = v.split("::");
  if (server_id) serverIdEl.value = server_id;
  if (session_id) sessionIdManualEl.value = session_id;
});

serverIdEl.value = localStorage.getItem("chronicle.server_id") || "";
apiBaseEl.value = localStorage.getItem("chronicle.api_base") || "";
apiBaseEl.addEventListener("change", () => localStorage.setItem("chronicle.api_base", apiBaseEl.value));

loadAuth();

