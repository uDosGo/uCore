export interface GridSymbolAttrs {
  char: string;
  fg: number;
  bg: number;
  span?: number;
}

interface SymbolEntry {
  shortcode: string;
  unicode: string;
  svg: string;
  grid?: GridSymbolAttrs;
}

const SYMBOLS: Record<string, SymbolEntry> = {
  heart: {
    shortcode: 'heart',
    unicode: '♥',
    svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill="currentColor" d="M8 14S2 10 2 6.5A3.5 3.5 0 0 1 8 4a3.5 3.5 0 0 1 6 2.5C14 10 8 14 8 14z"/></svg>',
    grid: { char: '♥', fg: 1, bg: 0, span: 1 },
  },
  rocket: {
    shortcode: 'rocket',
    unicode: '🚀',
    svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill="currentColor" d="M9 1c3 1 5 3 6 6l-3 2-4-4 1-4zM7 6l3 3-2 3-3 2-1-1 2-3 1-4zM2 14l2-1-1-1-1 2z"/></svg>',
    grid: { char: '▲', fg: 2, bg: 0, span: 1 },
  },
  star: {
    shortcode: 'star',
    unicode: '★',
    svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill="currentColor" d="M8 1l2 5h5l-4 3 2 5-5-3-5 3 2-5-4-3h5z"/></svg>',
    grid: { char: '★', fg: 3, bg: 0, span: 1 },
  },
  check: {
    shortcode: 'check',
    unicode: '✓',
    svg: '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16"><path fill="currentColor" d="M6.2 12.2L2.8 8.8l1.4-1.4 2 2 5.6-5.6 1.4 1.4z"/></svg>',
    grid: { char: '✓', fg: 2, bg: 0, span: 1 },
  },
};

function normalizeShortcode(value: string): string {
  const trimmed = value.trim();
  if (trimmed.startsWith(':') && trimmed.endsWith(':') && trimmed.length > 2) {
    return trimmed.slice(1, -1).toLowerCase();
  }
  return trimmed.toLowerCase();
}

export function resolveShortcode(shortcode: string): SymbolEntry | null {
  const key = normalizeShortcode(shortcode);
  return SYMBOLS[key] || null;
}

export function shortcodeToUnicode(shortcode: string): string {
  const entry = resolveShortcode(shortcode);
  if (!entry) return shortcode;
  return entry.unicode;
}

export function shortcodeToSVG(shortcode: string): string | null {
  const entry = resolveShortcode(shortcode);
  if (!entry) return null;
  return entry.svg;
}

export function shortcodeToGrid(shortcode: string): GridSymbolAttrs | null {
  const entry = resolveShortcode(shortcode);
  if (!entry || !entry.grid) return null;
  return entry.grid;
}
