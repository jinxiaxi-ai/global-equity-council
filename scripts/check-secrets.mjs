import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

const files = execFileSync("rg", [
  "--files",
  "-g",
  "!node_modules",
  "-g",
  "!.venv",
  "-g",
  "!dist",
  "-g",
  "!.git",
])
  .toString()
  .trim()
  .split("\n")
  .filter(Boolean);

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
