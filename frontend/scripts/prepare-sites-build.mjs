#!/usr/bin/env node
import { copyFileSync, cpSync, existsSync, mkdirSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dist = path.join(root, "dist");
const index = path.join(dist, "client", "index.html");
const worker = path.join(root, "worker", "index.js");
const hosting = path.join(root, ".openai", "hosting.json");
const notices = path.join(root, "public", "licenses");

for (const file of [index, worker, hosting, notices]) {
  if (!existsSync(file)) throw new Error("Missing Sites build input: " + file);
}
if (existsSync(path.join(dist, "client", "audio"))) {
  throw new Error("Private local audio must stay outside the web build. Check copyPublicDir.");
}
// Explicit public-asset allowlist; source imports are bundled by Vite itself.
cpSync(notices, path.join(dist, "client", "licenses"), { recursive: true });

mkdirSync(path.join(dist, "server"), { recursive: true });
mkdirSync(path.join(dist, ".openai"), { recursive: true });
copyFileSync(worker, path.join(dist, "server", "index.js"));
copyFileSync(hosting, path.join(dist, ".openai", "hosting.json"));

console.log("Prepared Sites build: dist/server/index.js and dist/.openai/hosting.json");
