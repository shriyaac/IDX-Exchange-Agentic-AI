// Week 4: per-user session memory (handbook's getSession / updateSession / clearSession).
// The handbook keeps sessions in a Map in memory. Our skills run as a fresh script for
// every message, so that Map would be empty each time. Instead, each session is saved
// as a small JSON file in ./sessions/ and survives between messages.
import fs from "node:fs";
import path from "node:path";

const DIR = path.join(path.dirname(new URL(import.meta.url).pathname), "sessions");

// Session shape (from the handbook's UserSession):
// { city, maxPrice, beds, baths, type, pool, hasView, lastResults, conversationStep }
const fileFor = userId =>
  path.join(DIR, String(userId || "default").replace(/[^A-Za-z0-9_-]/g, "_") + ".json");

export function getSession(userId) {
  try {
    return JSON.parse(fs.readFileSync(fileFor(userId), "utf8"));
  } catch {
    return { conversationStep: 0 };          // no session yet: start fresh
  }
}

export function updateSession(userId, updates) {
  const session = { ...getSession(userId), ...updates };
  fs.mkdirSync(DIR, { recursive: true });
  fs.writeFileSync(fileFor(userId), JSON.stringify(session, null, 2));
  return session;
}

export function clearSession(userId) {
  fs.rmSync(fileFor(userId), { force: true });
}

// Quick manual test:  node sessions.mjs test
if (import.meta.url === `file://${process.argv[1]}` && process.argv[2] === "test") {
  clearSession("demo");
  console.log("start:   ", getSession("demo"));
  console.log("update 1:", updateSession("demo", { city: "Irvine", conversationStep: 1 }));
  console.log("update 2:", updateSession("demo", { maxPrice: 1200000, conversationStep: 2 }));
  console.log("reloaded:", getSession("demo"));
  clearSession("demo");
  console.log("cleared: ", getSession("demo"));
}
