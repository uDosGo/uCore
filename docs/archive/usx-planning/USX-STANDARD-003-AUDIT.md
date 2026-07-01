# USX Standard v2 — Typography Audit Report

**Document ID:** USX-STANDARD-003-AUDIT  
**Date:** 2026-06-17  
**Status:** ✅ PASSED  
**Auditor:** Cline (automated)

---

## Audit Results

### Typography Check (Pico)
- [x] Headings use `<h1>`-`<h6>` (no custom classes)
- [x] Body text uses `<p>` (no custom classes)
- [x] Small text uses `<small>` (no custom classes)
- [x] Lists use `<ul>`/`<ol>` (no custom classes)
- [x] Code uses `<code>` (no custom classes)
- [x] Pico's default styles are visible and working

### Typography Check (USX Prose Baseline)
- [x] Markdown content is wrapped in `.prose`
- [x] Prose baseline is imported from `styles/prose-ui-standard.css`
- [x] Prose styles map to Pico tokens and avoid per-surface typography overrides

### Typography Violations
- [x] No custom CSS for headings (use Pico)
- [x] No custom CSS for body text (use Pico)
- [x] No per-surface custom CSS for markdown (use shared prose baseline)
- [x] No hardcoded font sizes
- [x] No hardcoded font families

---

## Files Audited

| File | Status | Notes |
|------|--------|-------|
| `styles/nestframe.css` | ✅ Clean | Pico import + prose baseline import + minimal NestFrame functional layers |
| `styles/prose-ui-standard.css` | ✅ Clean | Canonical markdown/prose baseline for `.prose` |
| `styles/tokens.css` | ✅ Clean | Only CSS variables, no typography overrides |
| `styles/surface-host.css` | ✅ Clean | Layout only |
| `styles/assistui.css` | ✅ Clean | Heading selectors defer to Pico defaults |
| `styles/userver.css` | ✅ Clean | Heading selectors defer to Pico defaults |
| `styles/hub/dashboard.css` | ✅ Clean | Heading selectors defer to Pico defaults |
| `styles/gridui-terminal.css` | ⏭️ Skipped | Terminal/teletext rendering — pixel-precise font sizes required for character alignment |
| `surfaces/browserui/styles/browserui.css` | ✅ Clean | Heading selectors defer to Pico defaults |
| `surfaces/proseui/styles/*.css` | ✅ Clean | Surface layout styles, not shared typography ownership |

---

## Passing Criteria

- [x] Zero custom styles for Pico-supported elements
- [x] Zero per-surface markdown typography overrides
- [x] Zero hardcoded font sizes (outside terminal/teletext)
- [x] Zero hardcoded font families
- [x] All typography comes from Pico or the shared prose baseline

---

## Summary

All surfaces pass the USX Standard v2 typography audit. Custom CSS has been removed from heading selectors across `assistui.css`, `userver.css`, `dashboard.css`, and `browserui.css`. Shared markdown rendering now routes through `styles/prose-ui-standard.css` to prevent per-surface prose drift. The only remaining pixel font sizes are in `gridui-terminal.css`, which is a terminal/teletext rendering surface that requires pixel-precise character alignment — this is an accepted exception per the standard's "only when needed" principle.

**NestFrame CSS** (`nestframe.css`) now contains only the key functional gaps that Pico and the shared prose baseline don't cover:
1. Grid system
2. uSystem pages
3. Controller focus
4. TV overrides
5. Mobile overrides
6. Minimal dark token overrides for UX consistency
