import http from "node:http";
import { decideWithAI, loadDotEnv } from "./ai-core.mjs";

const port = Number(process.env.PORT || 5173);

async function readBody(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8");
}

async function sendJson(response, status, data) {
  response.writeHead(status, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify(data, null, 2));
}

const server = http.createServer(async (request, response) => {
  try {
    if (request.method === "GET" && request.url === "/") {
      await sendJson(response, 200, {
        service: "Campus Companion AI API",
        endpoints: ["GET /api/health", "POST /api/ask"],
        example_body: { question: "Trua nay em an o dau duoc?" }
      });
      return;
    }

    if (request.method === "GET" && request.url === "/api/health") {
      await loadDotEnv();
      await sendJson(response, 200, {
        ok: true,
        provider: process.env.OPENAI_API_KEY ? "openai" : process.env.GEMINI_API_KEY ? "gemini" : process.env.ALLOW_MOCK_AI === "1" ? "mock" : "missing_key"
      });
      return;
    }

    if (request.method === "POST" && request.url === "/api/ask") {
      const body = JSON.parse(await readBody(request));
      if (!body.question || typeof body.question !== "string") {
        await sendJson(response, 400, { error: "question is required" });
        return;
      }

      const startedAt = Date.now();
      const decision = await decideWithAI(body.question);
      await sendJson(response, 200, {
        ...decision,
        latency_ms: Date.now() - startedAt
      });
      return;
    }

    response.writeHead(405);
    response.end("Method not allowed");
  } catch (error) {
    await sendJson(response, 500, { error: error.message });
  }
});

server.listen(port, () => {
  console.log(`Campus Companion AI API running at http://localhost:${port}`);
});
