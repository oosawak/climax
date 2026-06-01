const $ = (id) => document.getElementById(id);

const apiBaseEl = $("apiBase");
const apiCodeEl = $("apiCode");
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

async function copyToClipboard(value) {
  try {
    await navigator.clipboard.writeText(value);
    setStatus("copied");
  } catch {
    window.prompt("Copy to clipboard:\n(If prompt shows, copy manually)", value);
  }
}

async function postJson(url, body) {
  return fetchJson(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
}

function getSessionId() {
  const fromSelect = (sessionSelectEl.value || "").trim();
  if (fromSelect) return fromSelect;
  return (sessionIdManualEl.value || "").trim();
}

function apiUrl(path, params = {}) {
  const baseRaw = (apiBaseEl.value || "").trim();
  const isGitHubPages = location.hostname.endsWith("github.io");

  if (!baseRaw) {
    throw new Error("API base required (set Function App URL)");
  }

  if (isGitHubPages && baseRaw.startsWith("/")) {
    throw new Error("On GitHub Pages, API base must be an absolute URL (https://<functionapp>.azurewebsites.net/api)");
  }

  let baseInput = baseRaw.replace(/\/+$/, "");

  // Convenience: if user pasted just https://<app>.azurewebsites.net , append /api
  try {
    const parsed = new URL(baseInput);
    const host = (parsed.hostname || "").toLowerCase();
    const p = (parsed.pathname || "").replace(/\/+$/, "");
    if (host.endsWith("azurewebsites.net") && (!p || p === "/")) {
      baseInput = baseInput + "/api";
    }
  } catch {
    // ignore
  }
  const u = new URL(baseInput + "/" + path.replace(/^\/+/, ""), location.origin);

  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    u.searchParams.set(k, String(v));
  });

  const rawCode = (apiCodeEl.value || "").trim();
  if (rawCode && !u.searchParams.has("code")) {
    const code = rawCode.startsWith("?code=") ? rawCode.slice(6) : rawCode;
    u.searchParams.set("code", code);
  }

  return u.toString();
}

function fmtLog(it) {
  const ts = it.timestamp || "";
  const topic = it.topic ? ` [${it.topic}]` : "";
  const exit = (it.exit_code === 0 || it.exit_code) ? ` (exit=${it.exit_code})` : "";
  const cmd = it.command ? ` ${it.command}` : "";
  const nlp = it.nlp && it.nlp.intent ? ` {nlp:${it.nlp.intent}${it.nlp.provider ? ":" + it.nlp.provider : ""}}` : "";
  const head = `[${ts}]${topic}${exit}${cmd}${nlp}`.trim();
  const body = (it.log || "").trim();
  return `${head}\n${body}\n`;
}

async function fetchJson(url, opts = {}) {
  const res = await fetch(url, {
    ...opts,
    headers: { "Accept": "application/json", ...(opts.headers || {}) },
  });

  // Helpful errors for SWA auth / missing API
  const contentType = (res.headers.get("content-type") || "").toLowerCase();
  const looksJson = contentType.includes("application/json");

  if (res.status === 404) {
    throw new Error("404 Not Found: " + url + " (API not deployed yet, or API base is wrong)");
  }

  if (res.status === 401 || res.status === 403) {
    throw new Error("Unauthorized: " + url + " (please login)");
  }

  const txt = await res.text();

  if (!looksJson) {
    const hint = res.redirected && res.url.includes("/.auth/") ? " (auth redirect)" : "";
    throw new Error("Non-JSON response (" + res.status + ")" + hint + ": " + txt.slice(0, 200));
  }

  try {
    return JSON.parse(txt);
  } catch {
    throw new Error("Bad JSON (" + res.status + "): " + txt.slice(0, 200));
  }
}

async function loadAuth() {
  if (!authInfoEl) return;
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
  // `/api/logs/recent` が無い構成でも使えるように、sessions一覧を候補として表示する
  setStatus("sessions (as recent)...");
  const data = await fetchJson(apiUrl("sessions"));
  const items = data.items || [];

  recentSelectEl.innerHTML = "";
  for (const it of items) {
    const server_id = (it.server_id || "").trim();
    const session_id = (it.session_id || it.id || "").trim();
    if (!server_id || !session_id) continue;
    const opt = document.createElement("option");
    opt.value = server_id + "::" + session_id;
    opt.textContent = server_id + " / " + session_id;
    recentSelectEl.appendChild(opt);
  }

  setOut(JSON.stringify({ ok: true, items }, null, 2));
  setStatus("sessions: " + items.length);
}

async function sessionGet() {
  const server_id = serverIdEl.value.trim();
  const session_id = getSessionId();
  if (!server_id || !session_id) return;
  setStatus("session/get...");

  const data = await fetchJson(apiUrl("session/get", { server_id, session_id }));
  const item = data.item || null;

  const lines = [
    "session/get result (登録済みセッションの詳細)",
    "- directory: 作業ディレクトリ（復帰時の基準）",
    "- panes: tmuxのペイン情報（どのセッション/どのcwd/どんなコマンドか）",
    "",
    "raw:",
    JSON.stringify(data, null, 2),
  ];

  setOut(lines.join("\n"));
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
  const rendered = items.map(fmtLog).join("\n");
  setOut(rendered || "(no logs)");
  setStatus(`logs: ${items.length}`);
}

async function backfillNlp(dryRun) {
  const limit = parseInt(limitEl.value || "200", 10) || 200;
  const topic = topicEl.value.trim();
  setStatus(dryRun ? "backfill (dry-run)..." : "backfill...");
  const data = await postJson(apiUrl("logs/backfill_nlp"), {
    limit,
    topic: topic || undefined,
    dry_run: !!dryRun,
  });
  setOut(JSON.stringify(data, null, 2));
  setStatus("backfill: ok");
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
// GitHub Pages版ではログインUIを出さないため、存在する場合だけバインドします
const btnLogin = $("btnLogin");
if (btnLogin) {
  btnLogin.addEventListener("click", () => {
    location.href = "/.auth/login/aad";
  });
}

const btnLogout = $("btnLogout");
if (btnLogout) {
  btnLogout.addEventListener("click", () => {
    location.href = "/.auth/logout";
  });
}

$("btnSessions").addEventListener("click", loadSessions);
$("btnHealth").addEventListener("click", health);
$("btnSessionGet").addEventListener("click", sessionGet);
$("btnStatus").addEventListener("click", async () => {
  const server_id = serverIdEl.value.trim();
  const session_id = getSessionId();
  if (!server_id || !session_id) return;

  const topic = topicEl.value.trim();
  const limit = parseInt(limitEl.value || "50", 10) || 50;

  setStatus("status...");

  const sessionData = await fetchJson(apiUrl("session/get", { server_id, session_id }));
  const logsData = await fetchJson(apiUrl("logs", { server_id, session_id, limit, topic: topic || undefined }));
  const items = logsData.items || [];
  const rendered = items.map(fmtLog).join("\n") || "(no logs)";

  const lines = [
    "status result (セッション詳細 + 直近ログ)",
    "",
    "[session/get]",
    "- directory: 作業ディレクトリ",
    "- panes: tmuxのペイン情報",
    JSON.stringify(sessionData.item || sessionData, null, 2),
    "",
    `[logs] count=${items.length} (topic=${topic || "(all)"}, limit=${limit})`,
    rendered,
  ];

  setOut(lines.join("\n"));
  setStatus("status: ok");
});
$("btnLogs").addEventListener("click", loadLogsOnce);
$("btnFollow").addEventListener("click", follow);
$("btnStop").addEventListener("click", stopFollow);
$("btnCopyCtm").addEventListener("click", async () => {
  const sid = getSessionId();
  if (!sid) return alert("session_id required");
  await copyToClipboard(`./clients/ctm ${sid}`);
});
$("btnCopyCtmCmd").addEventListener("click", async () => {
  const sid = getSessionId();
  if (!sid) return alert("session_id required");
  await copyToClipboard(`./clients/ctm cmd ${sid}`);
});
$("btnCopyCtmLog").addEventListener("click", async () => {
  const sid = getSessionId();
  if (!sid) return alert("session_id required");
  await copyToClipboard(`./clients/ctm log ${sid}`);
});
$("btnBackfillDry").addEventListener("click", () => backfillNlp(true));
$("btnBackfill").addEventListener("click", () => backfillNlp(false));

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
apiCodeEl.value = localStorage.getItem("chronicle.api_code") || "";
apiCodeEl.addEventListener("change", () => localStorage.setItem("chronicle.api_code", apiCodeEl.value));

loadAuth();

// Auto-load something useful on open
try {
  // Only auto-load when API base is configured
  if ((apiBaseEl.value || "").trim()) loadRecentLogs();
  else setStatus("Set API base (Function App URL) then click Recent logs");
} catch (e) {
  setStatus(String(e && e.message ? e.message : e));
}


