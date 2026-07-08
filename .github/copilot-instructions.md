# uCore Development Rules

## USX Standard — NO Hardcoded Styles

All frontend components **MUST** use USX CSS custom properties. Never hardcode raw values.

### Color (`var(--usx-color-*)`)
| Token | Use |
|---|---|
| `--usx-color-on-surface` | Primary text |
| `--usx-color-on-surface-muted` | Secondary/muted text |
| `--usx-color-surface` | Card/surface backgrounds |
| `--usx-color-surface-variant` | Subtle backgrounds (code, muted areas) |
| `--usx-color-background` | Page background |
| `--usx-color-border` | Borders/dividers |
| `--usx-color-primary` | Interactive/active elements |
| `--usx-color-primary-hover` | Hover state |
| `--usx-color-success` | Success/complete status |
| `--usx-color-warning` | Warning/review status |
| `--usx-color-danger` | Error/blocked status |
| `--usx-color-info` | Info/neutral status |

### Spacing (`var(--usx-spacing-*)`)
`xs`(4px) `sm`(8px) `md`(12px) `lg`(16px) `xl`(24px) `2xl`(32px)

### Typography (`var(--usx-font-*)`)
**Sizes:** `xs` `sm` `base` `lg` `xl` `2xl` `3xl`
**Weights:** `--usx-font-weight-bold`(700) `--usx-font-weight-semibold`(600) `--usx-font-weight-medium`(500) `--usx-font-weight-regular`(400)
**Families:** `--usx-font-family-sans` `--usx-font-family-mono`

### Border Radius (`var(--usx-radius-*)`)
`sm` `md` `lg` `full` — **NOT** `--usx-border-radius-*`

### ❌ FORBIDDEN
- `--pico-*` variables (use `--usx-color-*` instead)
- Raw hex: `#f85149` → `var(--usx-color-danger)`
- Raw px/rem: `16px` → `var(--usx-spacing-lg)`
- Hardcoded font-weight: `font-weight: 600` → `var(--usx-font-weight-semibold)`
- Inline `style="..."` with hardcoded colors
- Emojis as UI icons → use `<UIcon name="..." />` Material Symbols

### Source of Truth
- Tokens: `frontend-vue/src/styles/tokens/tokens-{color,typography,spacing,touch,components}.css`
- Standard CSS: `frontend-vue/src/styles/usx-standard.css`
- Backend skill: `backend/app/skills/builtin/usx_standard.py`
