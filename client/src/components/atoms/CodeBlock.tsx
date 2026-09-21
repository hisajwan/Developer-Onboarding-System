export function CodeBlock({ code }: { code: string }) {
  return (
    <pre className="overflow-x-auto rounded-xl bg-code p-4 font-mono text-xs text-code-ink">
      <code>{code}</code>
    </pre>
  );
}
