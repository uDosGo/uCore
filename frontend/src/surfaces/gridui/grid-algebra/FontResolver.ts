/* ═══════════════════════════════════════════════════════════════════
   FontResolver — Maps fontId → Actual Font Rendering
   ═══════════════════════════════════════════════════════════════════
   Resolves font identifiers from the font manifest to actual
   CSS font-family values, bitmap font rendering, and emoji fallbacks.
   ═══════════════════════════════════════════════════════════════════ */

// ─── Types ──────────────────────────────────────────────────────

export type FontCategory = 'classic' | 'retro' | 'modern' | 'emoji';

export interface FontConfig {
  /** Font identifier (matches manifest.yaml) */
  id: string;
  /** Human-readable name */
  name: string;
  /** Font category */
  category: FontCategory;
  /** CSS font-family value */
  cssFamily: string;
  /** Whether this is a bitmap font (requires special rendering) */
  isBitmap: boolean;
  /** Cell size for bitmap fonts [width, height] */
  cellSize?: [number, number];
  /** Whether to use as fallback */
  fallback: boolean;
  /** CSS @font-face src URL or path */
  src?: string;
  /** Font weight */
  weight?: number;
  /** Font style */
  style?: 'normal' | 'italic';
}

// ─── Font Registry ─────────────────────────────────────────────

const fontRegistry: Map<string, FontConfig> = new Map();

// ─── Register Fonts ────────────────────────────────────────────

/**
 * Register a font configuration.
 */
export function registerFont(config: FontConfig): void {
  fontRegistry.set(config.id, config);
}

/**
 * Register multiple fonts at once.
 */
export function registerFonts(configs: FontConfig[]): void {
  for (const config of configs) {
    registerFont(config);
  }
}

// ─── Default Fonts ─────────────────────────────────────────────

/**
 * Initialise the font registry with default fonts.
 */
export function initFontRegistry(): void {
  registerFonts([
    // Classic bitmap fonts
    {
      id: 'ibm-vga',
      name: 'IBM VGA',
      category: 'classic',
      cssFamily: '"IBM VGA", monospace',
      isBitmap: true,
      cellSize: [8, 16],
      fallback: true,
    },
    {
      id: 'c64',
      name: 'Commodore 64',
      category: 'classic',
      cssFamily: '"C64", monospace',
      isBitmap: true,
      cellSize: [8, 8],
      fallback: false,
    },
    {
      id: 'zx-spectrum',
      name: 'ZX Spectrum',
      category: 'classic',
      cssFamily: '"ZX Spectrum", monospace',
      isBitmap: true,
      cellSize: [8, 8],
      fallback: false,
    },
    {
      id: 'teletext',
      name: 'Teletext',
      category: 'classic',
      cssFamily: '"Teletext", monospace',
      isBitmap: true,
      cellSize: [8, 10],
      fallback: true,
    },

    // Retro bitmap fonts
    {
      id: 'amiga-topaz',
      name: 'Amiga Topaz',
      category: 'retro',
      cssFamily: '"Amiga Topaz", monospace',
      isBitmap: true,
      cellSize: [8, 16],
      fallback: false,
    },
    {
      id: 'atari',
      name: 'Atari ST',
      category: 'retro',
      cssFamily: '"Atari ST", monospace',
      isBitmap: true,
      cellSize: [8, 16],
      fallback: false,
    },
    {
      id: 'msx',
      name: 'MSX',
      category: 'retro',
      cssFamily: '"MSX", monospace',
      isBitmap: true,
      cellSize: [8, 8],
      fallback: false,
    },

    // Modern fonts
    {
      id: 'inter',
      name: 'Inter',
      category: 'modern',
      cssFamily: '"Inter", system-ui, -apple-system, sans-serif',
      isBitmap: false,
      fallback: true,
    },
    {
      id: 'jetbrains-mono',
      name: 'JetBrains Mono',
      category: 'modern',
      cssFamily: '"JetBrains Mono", "Fira Code", monospace',
      isBitmap: false,
      fallback: true,
    },
    {
      id: 'fira-code',
      name: 'Fira Code',
      category: 'modern',
      cssFamily: '"Fira Code", monospace',
      isBitmap: false,
      fallback: false,
    },

    // Emoji fonts
    {
      id: 'noto-emoji-mono',
      name: 'Noto Emoji Monochrome',
      category: 'emoji',
      cssFamily: '"Noto Emoji", "Apple Color Emoji", "Segoe UI Emoji", sans-serif',
      isBitmap: false,
      fallback: true,
    },
    {
      id: 'noto-emoji-color',
      name: 'Noto Emoji Color',
      category: 'emoji',
      cssFamily: '"Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji", sans-serif',
      isBitmap: false,
      fallback: false,
    },
  ]);
}

// ─── Font Resolution ───────────────────────────────────────────

/**
 * Resolve a font ID to its FontConfig.
 */
export function resolveFont(fontId: string): FontConfig | undefined {
  return fontRegistry.get(fontId);
}

/**
 * Get the CSS font-family string for a font ID.
 */
export function getFontFamily(fontId: string): string {
  const font = resolveFont(fontId);
  return font?.cssFamily || 'monospace';
}

/**
 * Get all registered fonts.
 */
export function getAllFonts(): FontConfig[] {
  return Array.from(fontRegistry.values());
}

/**
 * Get fonts by category.
 */
export function getFontsByCategory(category: FontCategory): FontConfig[] {
  return getAllFonts().filter(f => f.category === category);
}

/**
 * Get fallback fonts (used when a specific font is unavailable).
 */
export function getFallbackFonts(): FontConfig[] {
  return getAllFonts().filter(f => f.fallback);
}

/**
 * Get the default font for a given context.
 */
export function getDefaultFont(context: 'gridui' | 'proseui' | 'terminal' | 'teletext'): string {
  switch (context) {
    case 'gridui':
    case 'teletext':
      return 'ibm-vga';
    case 'terminal':
      return 'jetbrains-mono';
    case 'proseui':
      return 'inter';
    default:
      return 'inter';
  }
}

// ─── CSS Generation ────────────────────────────────────────────

/**
 * Generate CSS @font-face declarations for all registered fonts.
 * This can be injected into the document head at runtime.
 */
export function generateFontFaceCSS(): string {
  let css = '';

  for (const font of getAllFonts()) {
    if (font.src) {
      css += `
@font-face {
  font-family: '${font.name}';
  src: url('${font.src}') format('${font.isBitmap ? 'bitmap' : 'truetype'}');
  font-weight: ${font.weight || 400};
  font-style: ${font.style || 'normal'};
  font-display: swap;
}
`;
    }
  }

  return css;
}

/**
 * Generate CSS for bitmap font rendering.
 * Bitmap fonts need exact pixel sizing to look correct.
 */
export function generateBitmapFontCSS(fontId: string): string {
  const font = resolveFont(fontId);
  if (!font || !font.isBitmap || !font.cellSize) return '';

  const [width, height] = font.cellSize;
  return `
.bitmap-font-${fontId} {
  font-family: ${font.cssFamily};
  font-size: ${height}px;
  line-height: ${height}px;
  letter-spacing: 0;
  font-feature-settings: "kern" 0;
  -webkit-font-smoothing: none;
  -moz-osx-font-smoothing: unset;
  font-smooth: never;
}
`;
}

// ─── Initialisation ────────────────────────────────────────────

// Auto-initialise on import
initFontRegistry();

export default {
  registerFont,
  registerFonts,
  resolveFont,
  getFontFamily,
  getAllFonts,
  getFontsByCategory,
  getFallbackFonts,
  getDefaultFont,
  generateFontFaceCSS,
  generateBitmapFontCSS,
};
