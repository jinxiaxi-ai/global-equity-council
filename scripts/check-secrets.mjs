import { execFileSync } from "node:child_process";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const ignoredNames = new Set([
  ".git",
  ".mypy_cache",
  ".npm-cache",
  ".pytest_cache",
  ".ruff_cache",
  ".venv",
  "__pycache__",
  "coverage",
  "dist",
  "node_modules",
  "playwright-report",
  "test-results",
]);

function trackedFiles() {
  try {
    return execFileSync("git", ["ls-files"])
      .toString()
      .trim()
      .split("\n")
      .filter(Boolean);
  } catch {
    return walk(".");
  }
}

function walk(directory) {
  const files = [];
  for (const entry of readdirSync(directory)) {
    if (ignoredNames.has(entry)) continue;
    const path = join(directory, entry);
    const stats = statSync(path);
    if (stats.isDirectory()) {
      files.push(...walk(path));
    } else if (stats.isFile()) {
      files.push(path);
    }
  }
  return files;
}

const files = trackedFiles();

const checks = [
  { name: "OpenAI key", regex: /\bsk-[A-Za-z0-9_-]{20,}\b/g },
  { name: "GitHub token", regex: /\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b/g },
  { name: "private key", regex: /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/g },
  { name: "AWS key", regex: /\bAKIA[A-Z0-9]{16}\b/g },
];

const findings = [];
for (const file of files) {
  if (file === "scripts/check-secrets.mjs") continue;
  let content;
  try {
    content = readFileSync(file, "utf8");
  } catch {
    continue;
  }
  for (const check of checks) {
    if (check.regex.test(content)) findings.push(`${file}: ${check.name}`);
    check.regex.lastIndex = 0;
  }
}

if (findings.length) {
  console.error(`Potential secrets detected:\n${findings.join("\n")}`);
  process.exit(1);
}
console.log(`Secret scan passed (${files.length} files checked).`);
