/* ═══════════════════════════════════════════════════════════════════
   CharacterSet — Teletext + Unicode + Custom Character Mapping
   ═══════════════════════════════════════════════════════════════════
   Maps between teletext character codes, Unicode code points,
   and shortcode symbols. Provides the bridge between GridUI's
   teletext rendering and the symbol registry.
   ═══════════════════════════════════════════════════════════════════ */

import { resolveShortcode, shortcodeToGrid, type GridSymbolAttrs } from '@/shared/symbols/registry';

// ─── Teletext Character Set ────────────────────────────────────

/**
 * Teletext G0 character set (basic Latin + graphics).
 * Maps teletext character codes (0-255) to Unicode code points.
 */
export const TELETEXT_G0: Record<number, string> = {
  // Control characters (0x00-0x1F) — mapped to space
  0x00: ' ', 0x01: ' ', 0x02: ' ', 0x03: ' ', 0x04: ' ', 0x05: ' ',
  0x06: ' ', 0x07: ' ', 0x08: ' ', 0x09: ' ', 0x0A: ' ', 0x0B: ' ',
  0x0C: ' ', 0x0D: ' ', 0x0E: ' ', 0x0F: ' ', 0x10: ' ', 0x11: ' ',
  0x12: ' ', 0x13: ' ', 0x14: ' ', 0x15: ' ', 0x16: ' ', 0x17: ' ',
  0x18: ' ', 0x19: ' ', 0x1A: ' ', 0x1B: ' ', 0x1C: ' ', 0x1D: ' ',
  0x1E: ' ', 0x1F: ' ',

  // Basic Latin (0x20-0x7E)
  0x20: ' ', 0x21: '!', 0x22: '"', 0x23: '#', 0x24: '$', 0x25: '%',
  0x26: '&', 0x27: "'", 0x28: '(', 0x29: ')', 0x2A: '*', 0x2B: '+',
  0x2C: ',', 0x2D: '-', 0x2E: '.', 0x2F: '/', 0x30: '0', 0x31: '1',
  0x32: '2', 0x33: '3', 0x34: '4', 0x35: '5', 0x36: '6', 0x37: '7',
  0x38: '8', 0x39: '9', 0x3A: ':', 0x3B: ';', 0x3C: '<', 0x3D: '=',
  0x3E: '>', 0x3F: '?', 0x40: '@', 0x41: 'A', 0x42: 'B', 0x43: 'C',
  0x44: 'D', 0x45: 'E', 0x46: 'F', 0x47: 'G', 0x48: 'H', 0x49: 'I',
  0x4A: 'J', 0x4B: 'K', 0x4C: 'L', 0x4D: 'M', 0x4E: 'N', 0x4F: 'O',
  0x50: 'P', 0x51: 'Q', 0x52: 'R', 0x53: 'S', 0x54: 'T', 0x55: 'U',
  0x56: 'V', 0x57: 'W', 0x58: 'X', 0x59: 'Y', 0x5A: 'Z', 0x5B: '[',
  0x5C: '\\', 0x5D: ']', 0x5E: '^', 0x5F: '_', 0x60: '`', 0x61: 'a',
  0x62: 'b', 0x63: 'c', 0x64: 'd', 0x65: 'e', 0x66: 'f', 0x67: 'g',
  0x68: 'h', 0x69: 'i', 0x6A: 'j', 0x6B: 'k', 0x6C: 'l', 0x6D: 'm',
  0x6E: 'n', 0x6F: 'o', 0x70: 'p', 0x71: 'q', 0x72: 'r', 0x73: 's',
  0x74: 't', 0x75: 'u', 0x76: 'v', 0x77: 'w', 0x78: 'x', 0x79: 'y',
  0x7A: 'z', 0x7B: '{', 0x7C: '|', 0x7D: '}', 0x7E: '~', 0x7F: ' ',

  // Teletext graphics block characters (0x80-0xFF)
  // These are mosaic/block graphics used for teletext art
  0x80: ' ', 0x81: '⢀', 0x82: '⢠', 0x83: '⢰', 0x84: '⢸', 0x85: '⡀',
  0x86: '⣀', 0x87: '⣠', 0x88: '⣰', 0x89: '⣸', 0x8A: '⡄', 0x8B: '⣄',
  0x8C: '⣤', 0x8D: '⣴', 0x8E: '⣼', 0x8F: '⡆', 0x90: '⣆', 0x91: '⣦',
  0x92: '⣶', 0x93: '⣾', 0x94: '⡇', 0x95: '⣇', 0x96: '⣧', 0x97: '⣷',
  0x98: '⣿', 0x99: '⢁', 0x9A: '⣁', 0x9B: '⣡', 0x9C: '⣱', 0x9D: '⣹',
  0x9E: '⢅', 0x9F: '⣅', 0xA0: '⣥', 0xA1: '⣵', 0xA2: '⣽', 0xA3: '⢃',
  0xA4: '⣃', 0xA5: '⣣', 0xA6: '⣳', 0xA7: '⣻', 0xA8: '⢇', 0xA9: '⣇',
  0xAA: '⣧', 0xAB: '⣷', 0xAC: '⣿', 0xAD: '⢉', 0xAE: '⣉', 0xAF: '⣩',
  0xB0: '⣹', 0xB1: '⣹', 0xB2: '⣍', 0xB3: '⣭', 0xB4: '⣽', 0xB5: '⣽',
  0xB6: '⢋', 0xB7: '⣋', 0xB8: '⣫', 0xB9: '⣻', 0xBA: '⣻', 0xBB: '⢏',
  0xBC: '⣏', 0xBD: '⣯', 0xBE: '⣿', 0xBF: '⣿', 0xC0: '▘', 0xC1: '▝',
  0xC2: '▀', 0xC3: '▗', 0xC4: '▖', 0xC5: '▄', 0xC6: '▌', 0xC7: '▐',
  0xC8: '▚', 0xC9: '▞', 0xCA: '█', 0xCB: '▛', 0xCC: '▜', 0xCD: '▟',
  0xCE: '▙', 0xCF: '▀', 0xD0: '▔', 0xD1: '▁', 0xD2: '▂', 0xD3: '▃',
  0xD4: '▄', 0xD5: '▅', 0xD6: '▆', 0xD7: '▇', 0xD8: '█', 0xD9: '▉',
  0xDA: '▊', 0xDB: '▋', 0xDC: '▌', 0xDD: '▍', 0xDE: '▎', 0xDF: '▏',
  0xE0: '▕', 0xE1: '◢', 0xE2: '◣', 0xE3: '◤', 0xE4: '◥', 0xE5: '◰',
  0xE6: '◱', 0xE7: '◲', 0xE8: '◳', 0xE9: '◴', 0xEA: '◵', 0xEB: '◶',
  0xEC: '◷', 0xED: '◸', 0xEE: '◹', 0xEF: '◺', 0xF0: '◻', 0xF1: '◼',
  0xF2: '◽', 0xF3: '◾', 0xF4: '◿', 0xF5: '─', 0xF6: '━', 0xF7: '│',
  0xF8: '┃', 0xF9: '┌', 0xFA: '┐', 0xFB: '└', 0xFC: '┘', 0xFD: '├',
  0xFE: '┤', 0xFF: '┼',
};

// ─── Character Resolution ──────────────────────────────────────

export interface ResolvedChar {
  /** The character to display */
  char: string;
  /** Foreground colour index */
  fg: number;
  /** Background colour index */
  bg: number;
  /** Whether this is a shortcode symbol */
  isSymbol: boolean;
  /** Original shortcode if applicable */
  shortcode?: string;
  /** Cell span (for wide characters) */
  span: number;
}

/**
 * Resolve a character from a teletext code, Unicode char, or shortcode.
 *
 * @param input - Teletext code (number), Unicode character (string), or shortcode (":name:")
 * @returns Resolved character with colour attributes
 */
export function resolveCharacter(
  input: number | string,
  defaultFg = 7,
  defaultBg = 0
): ResolvedChar {
  // Shortcode resolution
  if (typeof input === 'string' && input.startsWith(':') && input.endsWith(':')) {
    const shortcode = input.slice(1, -1);
    const grid = shortcodeToGrid(shortcode);
    if (grid) {
      return {
        char: grid.char,
        fg: grid.fg,
        bg: grid.bg,
        isSymbol: true,
        shortcode,
        span: grid.span || 1,
      };
    }

    // Fallback: try unicode from registry
    const entry = resolveShortcode(shortcode);
    if (entry?.unicode) {
      return {
        char: entry.unicode,
        fg: defaultFg,
        bg: defaultBg,
        isSymbol: true,
        shortcode,
        span: entry.unicode.length > 1 ? 2 : 1,
      };
    }

    // Unknown shortcode — render as text
    return {
      char: input,
      fg: defaultFg,
      bg: defaultBg,
      isSymbol: false,
      span: input.length,
    };
  }

  // Teletext code resolution
  if (typeof input === 'number') {
    const char = TELETEXT_G0[input] || ' ';
    return {
      char,
      fg: defaultFg,
      bg: defaultBg,
      isSymbol: false,
      span: 1,
    };
  }

  // Direct character
  return {
    char: input,
    fg: defaultFg,
    bg: defaultBg,
    isSymbol: false,
    span: input.length > 1 ? 2 : 1,
  };
}

/**
 * Resolve a string containing shortcodes and text into an array of ResolvedChar.
 * Used by GridUI to render teletext pages with embedded symbols.
 */
export function resolveString(input: string, defaultFg = 7, defaultBg = 0): ResolvedChar[] {
  const result: ResolvedChar[] = [];
  const regex = /(:[a-zA-Z0-9_+-]+:)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(input)) !== null) {
    // Add text before this match
    if (match.index > lastIndex) {
      const text = input.slice(lastIndex, match.index);
      for (const char of text) {
        result.push({
          char,
          fg: defaultFg,
          bg: defaultBg,
          isSymbol: false,
          span: 1,
        });
      }
    }

    // Add resolved shortcode
    result.push(resolveCharacter(match[1], defaultFg, defaultBg));
    lastIndex = regex.lastIndex;
  }

  // Add remaining text
  if (lastIndex < input.length) {
    const text = input.slice(lastIndex);
    for (const char of text) {
      result.push({
        char,
        fg: defaultFg,
        bg: defaultBg,
        isSymbol: false,
        span: 1,
      });
    }
  }

  return result;
}

export default {
  TELETEXT_G0,
  resolveCharacter,
  resolveString,
};
