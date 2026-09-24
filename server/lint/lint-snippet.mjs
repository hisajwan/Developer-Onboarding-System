// Lints one pasted snippet with ESLint's Linter API: no project, no tsconfig, no import resolution.
// Reads {"code": string, "filename": string} as JSON on stdin and writes
// {"messages": [{rule_id, message, line, column, severity}]} as JSON on stdout.
// A snippet that does not parse comes back as one message with rule_id null.

import { Linter } from "eslint";
import jsxA11y from "eslint-plugin-jsx-a11y";
import react from "eslint-plugin-react";
import reactHooks from "eslint-plugin-react-hooks";
import tseslint from "typescript-eslint";

const config = [
  {
    files: ["**/*.{js,jsx,ts,tsx}"],
    languageOptions: {
      parser: tseslint.parser,
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: { ecmaFeatures: { jsx: true } },
    },
    plugins: {
      "@typescript-eslint": tseslint.plugin,
      "jsx-a11y": jsxA11y,
      react,
      "react-hooks": reactHooks,
    },
    settings: { react: { version: "19.0" } },
    rules: {
      ...jsxA11y.flatConfigs.recommended.rules,
      "react-hooks/rules-of-hooks": "error",
      "react-hooks/exhaustive-deps": "warn",
      "react/jsx-key": "error",
      "react/no-array-index-key": "warn",
      "react/jsx-no-target-blank": "warn",
      "react/no-unescaped-entities": "warn",
      "react/self-closing-comp": "warn",
      // A snippet usually defines a component and never uses it, so capitalised names are exempt.
      "@typescript-eslint/no-unused-vars": ["warn", { varsIgnorePattern: "^[A-Z]", args: "after-used" }],
      "@typescript-eslint/no-explicit-any": "warn",
      eqeqeq: ["warn", "smart"],
      "prefer-const": "warn",
      "no-var": "warn",
      "no-console": "warn",
      "no-debugger": "error",
      // Security: code execution from strings, raw HTML, javascript: URLs.
      "no-eval": "error",
      "no-implied-eval": "error",
      "no-new-func": "error",
      "no-script-url": "error",
      "react/no-danger": "warn",
      "react/jsx-no-script-url": "error",
    },
  },
];

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString("utf8");
}

const { code, filename } = JSON.parse(await readStdin());
const linter = new Linter({ configType: "flat" });
const messages = linter.verify(code, config, { filename }).map((message) => ({
  rule_id: message.ruleId ?? null,
  // Drop our own config detail ("Allowed unused vars must match /^[A-Z]/u.") from the message.
  message: message.message.replace(/ Allowed unused \w+ must match .*$/, ""),
  line: message.line ?? null,
  column: message.column ?? null,
  severity: message.severity === 2 ? "error" : "warning",
}));
process.stdout.write(JSON.stringify({ messages }));
