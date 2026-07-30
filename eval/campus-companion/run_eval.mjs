import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { decideWithAI } from "../../campus-companion/ai-core.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const goldenPath = path.join(__dirname, "golden_set.json");

if (process.argv.includes("--mock")) {
  process.env.ALLOW_MOCK_AI = "1";
}

const cases = JSON.parse(await fs.readFile(goldenPath, "utf8"));
const results = [];

for (const testCase of cases) {
  const startedAt = Date.now();
  try {
    const { provider, result } = await decideWithAI(testCase.input);
    const decisionPass = result.decision === testCase.expected_decision;
    const intentPass = result.intent === testCase.expected_intent;

    results.push({
      ...testCase,
      provider,
      actual_intent: result.intent,
      actual_decision: result.decision,
      confidence: result.confidence,
      answer: result.answer,
      source: result.source,
      latency_ms: Date.now() - startedAt,
      decision_pass: decisionPass,
      intent_pass: intentPass,
      pass: decisionPass && intentPass
    });
  } catch (error) {
    results.push({
      ...testCase,
      provider: "none",
      actual_intent: null,
      actual_decision: null,
      confidence: null,
      answer: null,
      source: null,
      latency_ms: Date.now() - startedAt,
      decision_pass: false,
      intent_pass: false,
      pass: false,
      error: error.message
    });
  }
}

const total = results.length;
const passed = results.filter((item) => item.pass).length;
const decisionPassed = results.filter((item) => item.decision_pass).length;
const intentPassed = results.filter((item) => item.intent_pass).length;
const provider = results.find((item) => item.provider !== "none")?.provider || "none";
const summary = {
  ran_at: new Date().toISOString(),
  provider,
  total,
  passed,
  pass_rate: Number((passed / total).toFixed(3)),
  decision_passed: decisionPassed,
  decision_pass_rate: Number((decisionPassed / total).toFixed(3)),
  intent_passed: intentPassed,
  intent_pass_rate: Number((intentPassed / total).toFixed(3)),
  quality_bar: "Dat khi decision_pass_rate >= 0.80 va khong answer cho case can escalate."
};

const output = { summary, results };
const outputPath = path.join(__dirname, `results-${summary.ran_at.replace(/[:.]/g, "-")}.json`);
await fs.writeFile(outputPath, `${JSON.stringify(output, null, 2)}\n`, "utf8");

console.table(results.map((item) => ({
  id: item.id,
  expected: item.expected_decision,
  actual: item.actual_decision || "error",
  intent: item.actual_intent || "error",
  pass: item.pass
})));
console.log(`\nSummary: ${passed}/${total} full pass, ${decisionPassed}/${total} decision pass.`);
console.log(`Saved: ${outputPath}`);
