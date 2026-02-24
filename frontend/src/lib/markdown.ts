/** Extract the first H1 title from markdown content */
export function extractTitle(content: string): string {
  const match = content.match(/^#\s+(.+)$/m);
  return match ? match[1].trim() : "Sin título";
}

/** Extract a plain-text excerpt from markdown (first paragraph after title) */
export function extractExcerpt(content: string, maxLength = 200): string {
  const lines = content.split("\n");
  let pastTitle = false;

  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith("# ")) {
      pastTitle = true;
      continue;
    }
    if (pastTitle && stripped && !stripped.startsWith("#")) {
      const clean = stripped
        .replace(/[*_`[\]]/g, "")
        .replace(/\(http[^)]+\)/g, "")
        .replace(/!\[.*?\]/g, "");
      return clean.length > maxLength
        ? clean.slice(0, maxLength) + "..."
        : clean;
    }
  }

  return "";
}

/** Count words in markdown content */
export function countWords(content: string): number {
  return content.split(/\s+/).filter(Boolean).length;
}
