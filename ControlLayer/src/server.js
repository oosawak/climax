import http from "node:http";
import { MongoClient } from "mongodb";

const PORT = Number.parseInt(process.env.PORT ?? "3000", 10);
const MONGODB_URI = process.env.MONGODB_URI ?? "mongodb://127.0.0.1:27017";
const MONGODB_DB = process.env.MONGODB_DB ?? "climax_control_layer";

const client = new MongoClient(MONGODB_URI);
let db = null;

async function connectMongo() {
  if (db) {
    return db;
  }

  await client.connect();
  db = client.db(MONGODB_DB);
  await db.command({ ping: 1 });
  return db;
}

function sendJson(res, statusCode, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(statusCode, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body),
  });
  res.end(body);
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);

  if (req.method === "GET" && url.pathname === "/health") {
    sendJson(res, 200, {
      ok: true,
      service: "climax-control-layer",
      mongo: Boolean(db),
    });
    return;
  }

  if (req.method === "GET" && url.pathname === "/db/ping") {
    try {
      const database = await connectMongo();
      await database.command({ ping: 1 });
      sendJson(res, 200, {
        ok: true,
        mongo: "connected",
        db: MONGODB_DB,
      });
    } catch (error) {
      sendJson(res, 500, {
        ok: false,
        mongo: "error",
        message: error instanceof Error ? error.message : String(error),
      });
    }
    return;
  }

  sendJson(res, 404, {
    ok: false,
    error: "not_found",
  });
});

async function shutdown() {
  try {
    server.close(() => {});
    await client.close();
  } finally {
    process.exit(0);
  }
}

process.on("SIGINT", () => {
  void shutdown("SIGINT");
});

process.on("SIGTERM", () => {
  void shutdown("SIGTERM");
});

await connectMongo();

server.listen(PORT, () => {
  console.log(`Climax Control Layer listening on http://127.0.0.1:${PORT}`);
  console.log(`MongoDB connected to ${MONGODB_URI}/${MONGODB_DB}`);
});
