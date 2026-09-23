export function pluralChunks(count: number): string {
  return `${count} chunk${count === 1 ? "" : "s"}`;
}
