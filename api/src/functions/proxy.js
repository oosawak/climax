const { app } = require("@azure/functions");

function _joinUrl(base, pathAndQuery) {
  const b = (base || "").replace(/\/+$/, "");
  const p = (pathAndQuery || "").replace(/^\/+/, "");
  return b + "/" + p;
}

async function _readBody(request) {
  const method = (request.method || "GET").toUpperCase();
  if (method === "GET" || method === "HEAD") return undefined;
  try {
    return await request.text();
  } catch {
    return undefined;
  }
}

function _copyHeaders(request) {
  const headers = {};
  for (const [k, v] of request.headers.entries()) {
    const key = String(k || "").toLowerCase();
    if (!key) continue;
    if (key === "host") continue;
    if (key === "content-length") continue;
    headers[key] = v;
  }
  return headers;
}

app.http("proxy", {
  route: "{*path}",
  methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
  authLevel: "anonymous",
  handler: async (request, context) => {
    const backendBase = process.env.CHRONICLE_BACKEND_URL || "";
    if (!backendBase) {
      return { status: 500, jsonBody: { ok: false, error: "missing env: CHRONICLE_BACKEND_URL" } };
    }

    const backendCode = process.env.CHRONICLE_BACKEND_CODE || "";
    const incoming = new URL(request.url);
    const path = incoming.pathname.replace(/^\/api\/?/, "");
    const outUrl = new URL(_joinUrl(backendBase, path));

    // forward query params
    for (const [k, v] of incoming.searchParams.entries()) outUrl.searchParams.append(k, v);
    if (backendCode && !outUrl.searchParams.has("code")) outUrl.searchParams.set("code", backendCode);

    // forward request
    const body = await _readBody(request);
    const headers = _copyHeaders(request);
    if (body !== undefined && !headers["content-type"]) {
      // keep backend friendly; caller normally sets this
      headers["content-type"] = "application/json";
    }

    // CORS preflight passthrough
    if ((request.method || "").toUpperCase() === "OPTIONS") {
      return {
        status: 204,
        headers: {
          "access-control-allow-origin": "*",
          "access-control-allow-methods": "GET,POST,PUT,PATCH,DELETE,OPTIONS,HEAD",
          "access-control-allow-headers": "content-type,authorization",
        },
      };
    }

    context.log(`proxy -> ${outUrl.toString()}`);
    const res = await fetch(outUrl.toString(), {
      method: request.method,
      headers,
      body,
      redirect: "manual",
    });

    const resHeaders = {};
    for (const [k, v] of res.headers.entries()) {
      const key = String(k || "").toLowerCase();
      if (!key) continue;
      if (key === "transfer-encoding") continue;
      resHeaders[key] = v;
    }

    const resText = await res.text();
    const ct = (resHeaders["content-type"] || "").toLowerCase();
    if (ct.includes("application/json")) {
      try {
        return { status: res.status, headers: resHeaders, jsonBody: JSON.parse(resText || "null") };
      } catch {
        return { status: res.status, headers: resHeaders, body: resText };
      }
    }
    return { status: res.status, headers: resHeaders, body: resText };
  },
});

