#!/usr/bin/env node
/**
 * migrate-usx.cjs — Replace all --usx-* CSS custom properties with --pico-* equivalents
 * Handles both var(--usx-*) usage and bare --usx-* property definitions.
 * Run: node migrate-usx.cjs
 */
const fs = require('fs')
const path = require('path')

// Map of --usx-* token names to their --pico-* replacements
const TOKEN_MAP = {
  // Colors
  '--usx-color-tertiary': '--pico-ins-color',
  '--usx-color-on-surface-variant': '--pico-muted-color',
  '--usx-color-outline': '--pico-border-color',
  '--usx-color-error': '--pico-del-color',
  '--usx-color-primary': '--pico-primary',
  '--usx-color-surface-container': '--pico-card-background-color',
  '--usx-color-tertiary-container': '--pico-ins-color',
  '--usx-color-primary-container': '--pico-primary',
  '--usx-color-on-surface': '--pico-color',
  '--usx-color-on-primary': '--pico-primary-inverse',
  '--usx-color-surface': '--pico-background-color',
  '--usx-color-error-container': '--pico-del-color',
  '--usx-color-on-primary-container': '--pico-primary',
  '--usx-color-on-error-container': '--pico-del-color',
  '--usx-color-on-tertiary-container': '--pico-ins-color',
  '--usx-color-surface-variant': '--pico-card-sectioning-background-color',
  '--usx-color-outline-variant': '--pico-border-color',
  '--usx-color-surface-container-high': '--pico-card-sectioning-background-color',
  '--usx-color-success': '--pico-ins-color',
  // Typography
  '--usx-type-em': '1rem',
  '--usx-type-2xl': '1.5rem',
  '--usx-type-md': '0.9rem',
  '--usx-type-sm': '0.8rem',
  '--usx-type-xs': '0.7rem',
  '--usx-type-base': '0.85rem',
  '--usx-type-2xs': '0.65rem',
  // Radii
  '--usx-radius-md': '--pico-border-radius',
  // Fonts
  '--usx-font-mono': '--pico-font-family',
  // Shadows
  '--usx-shadow-sm': '--pico-box-shadow',
  '--usx-shadow-md': '--pico-box-shadow',
  '--usx-shadow-lg': '--pico-box-shadow',
  // Transitions
  '--usx-transition': '150ms ease',
}

// Build replacement patterns: both var(--usx-*) and bare --usx-*
const REPLACEMENTS = []
for (const [usxToken, picoToken] of Object.entries(TOKEN_MAP)) {
  // var(--usx-xxx) -> var(--pico-xxx, fallback)
  const varPattern = new RegExp(`var\\(${escapeRegex(usxToken)}\\)`, 'g')
  const varReplacement = picoToken.startsWith('--')
    ? `var(${picoToken}, #30363d)`
    : picoToken
  REPLACEMENTS.push([varPattern, varReplacement])

  // bare --usx-xxx: -> --pico-xxx (for CSS property definitions)
  const barePattern = new RegExp(escapeRegex(usxToken), 'g')
  REPLACEMENTS.push([barePattern, picoToken])
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

const SRC_DIR = path.resolve(__dirname)

function walkDir(dir) {
  const files = []
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true })
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name)
      if (entry.isDirectory() && !entry.name.startsWith('.') && entry.name !== 'node_modules') {
        files.push(...walkDir(fullPath))
      } else if (entry.isFile() && (entry.name.endsWith('.tsx') || entry.name.endsWith('.ts') || entry.name.endsWith('.css'))) {
        files.push(fullPath)
      }
    }
  } catch (e) {
    // skip
  }
  return files
}

const files = walkDir(SRC_DIR)
let totalFixed = 0
let totalFiles = 0

for (const file of files) {
  let content = fs.readFileSync(file, 'utf-8')
  let original = content
  for (const [pattern, replacement] of REPLACEMENTS) {
    content = content.replace(pattern, replacement)
  }
  if (content !== original) {
    // Count how many replacements
    let count = 0
    for (const [pattern] of REPLACEMENTS) {
      const matches = original.match(pattern)
      if (matches) count += matches.length
    }
    fs.writeFileSync(file, content, 'utf-8')
    totalFixed += count
    totalFiles++
    console.log(`  ✓ ${path.relative(SRC_DIR, file)} (${count} replacements)`)
  }
}

console.log(`\nDone! ${totalFiles} files updated, ${totalFixed} total replacements.`)
