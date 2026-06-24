# USX Developer Workflow Guide
**Status:** Active Standard  
**Version:** 2.0 (Skill-Integrated)  
**Last Updated:** 2026-06-24

---

## Quick Start (5 min)

### For New Surfaces
```bash
# 1. Create new surface CSS
touch frontend/src/styles/surfaces/mynewsurface.css

# 2. Bootstrap it with standards
# Use skills: skill_usx_bootstrap_surface
# Or manually: copy template from USX-SKILLS-REFACTOR-STRATEGY.md

# 3. Reference these in your CSS
padding: var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal);
background: var(--pico-card-background-color);
gap: var(--usx-card-gap);

# 4. Test locally
npm run dev  # Should see standardized spacing/colors

# 5. Audit before commit
npm run audit:usx-style -- surfaces/mynewsurface.css
```

### For Existing Surface Updates
```bash
# 1. Make your component changes
# 2. Use spacing variables, not hardcoded px
# 3. Run audit
npm run audit:usx-style -- surfaces/mychanges.css

# 4. If violations: Run repair skill
# skill_usx_color_reset or skill_usx_spacing_normalize

# 5. Visual test, commit, done
```

---

## Daily Development Workflow

### Phase 1: Starting Work

```yaml
Task: Add new component to workflow surface

1. Create branch:
   git checkout -b feature/workflow-new-component

2. Edit: surfaces/workflow.css
   Add new component class

3. Check requirements:
   ✓ Using var(--usx-*) for spacing?
   ✓ Using var(--pico-*) for colors?
   ✓ Padding follows standard (14/16px)?
   ✓ Gap uses standard values (4/8/12/16/24px)?

4. Dev server:
   npm run dev
   → Navigate to /workflow
   → Check visual appearance

5. Compare to reference:
   - Do cards align with other cards?
   - Are gaps consistent?
   - No unexpected whitespace?
```

### Phase 2: Code Review Prep

```yaml
Before pushing PR:

1. Run audit:
   npm run audit:usx-style -- surfaces/workflow.css
   Expected: conformance_score >= 95%

2. Check git diff:
   git diff surfaces/workflow.css
   - Any hardcoded #hex colors? ✗ Fix
   - Any hardcoded px in padding? ✗ Fix
   - Any new px font sizes? ✗ Check against Pico

3. Commit message includes:
   - What changed (component name)
   - Why (feature, fix, refactor)
   - Conformance status: ✓ PASS or ⚠️ 85% (with explanation)

4. Example commit:
   "feat(workflow): add priority filter component
   
   - New filter card using standard component pattern
   - Padding: var(--usx-card-padding-vertical/horizontal)
   - Gap: var(--usx-card-gap)
   - Spacing audit: 98% conformance"
```

### Phase 3: PR Description Template

```markdown
## USX Styling Checklist

- [ ] No hardcoded hex colors (except Pico fallbacks)
- [ ] All padding/margin uses var(--usx-*)
- [ ] All colors use var(--pico-*) with fallbacks
- [ ] Gap values only from: 4, 8, 12, 16, 24px
- [ ] No nested div double-padding
- [ ] Visual test: no layout shift
- [ ] Audit result: >= 95% conformance
- [ ] Components follow usx-spacing-scale.css patterns

### Audit Results
```
surface: workflow
conformance_score: 0.98
violations: 0
```

### Visual Test Evidence
<screenshots or description>
```

---

## Component Reference (Copy-Paste Ready)

### Standard Card
```css
.{surface}-card {
  padding: var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal);
  display: flex;
  flex-direction: column;
  gap: var(--usx-card-gap);
  background: var(--pico-card-background-color, #161b22);
  border: 1px solid var(--pico-border-color, #30363d);
  border-radius: 8px;
}
```

### Standard Section
```css
.{surface}-section {
  padding: var(--usx-section-padding);
  display: flex;
  flex-direction: column;
  gap: var(--usx-section-gap);
  margin-bottom: var(--usx-spacing-lg);
}
```

### Standard Button
```css
.{surface}-button {
  padding: var(--usx-button-padding-vertical) var(--usx-button-padding-horizontal);
  border: 1px solid var(--pico-border-color, #30363d);
  background: var(--pico-card-background-color, #161b22);
  color: var(--pico-color, #c9d1d9);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.{surface}-button:hover {
  border-color: var(--pico-primary, #58a6ff);
  background: rgba(88, 166, 255, 0.08);
}
```

### Standard Badge
```css
.{surface}-badge {
  padding: var(--usx-badge-padding-vertical) var(--usx-badge-padding-horizontal);
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: var(--pico-card-sectioning-background-color, #1c2128);
  color: var(--pico-muted-color, #8b949e);
  font-size: 0.875rem;
  white-space: nowrap;
}

.{surface}-badge--active {
  background: rgba(88, 166, 255, 0.15);
  color: var(--pico-primary, #58a6ff);
  border: 1px solid var(--pico-primary, #58a6ff);
}
```

### Standard Grid
```css
.{surface}-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--usx-grid-gap);
}

.{surface}-grid--dense {
  gap: var(--usx-grid-gap-dense);
}

.{surface}-grid--loose {
  gap: var(--usx-grid-gap-loose);
}
```

### Standard Flex Row
```css
.{surface}-flex-row {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: var(--usx-spacing-sm);
}
```

---

## Troubleshooting

### Issue: Component has too much/too little whitespace

**Check:**
1. Is padding using `var(--usx-*)`? →  YES: Check which variable
2. What's the value?
   - Card padding: 14px vertical, 16px horizontal ✓
   - Section padding: 16px all sides ✓
   - Other: Should match one of the 6-value scale

**Fix:**
```
Before:
  padding: 20px;  ← Non-standard

After:
  padding: var(--usx-spacing-lg);  ← 16px standard
  margin-bottom: var(--usx-spacing-md);  ← Add margin sep if needed
```

### Issue: Colors don't match design

**Check:**
1. Using `var(--pico-*)`? If YES → colors are from Pico (correct)
2. If NO → hardcoded hex detected

**Fix:**
```
Before:
  background: #161b22;  ← Hardcoded
  color: #c9d1d9;

After:
  background: var(--pico-card-background-color, #161b22);
  color: var(--pico-color, #c9d1d9);
```

### Issue: Gaps look uneven

**Check:**
1. What gap values are you using?
   - Valid: 4px, 8px, 12px, 16px, 24px only
   - Invalid: 6px, 10px, 14px, 20px, etc.

**Fix:**
```
Before:
  gap: 6px;   ← Non-standard, closest is 8px
  gap: 10px;  ← Non-standard, closest is 8px or 12px
  gap: 20px;  ← Non-standard, closest is 16px or 24px

After:
  gap: var(--usx-spacing-xs);   ← 4px
  gap: var(--usx-spacing-sm);   ← 8px
  gap: var(--usx-spacing-md);   ← 12px
  gap: var(--usx-spacing-lg);   ← 16px
```

### Issue: Nested elements have too much padding

**Check:**
```
.panel { padding: 16px; }
.panel-header { padding-bottom: 4px; }  ← DOUBLE SPACE!
```

**Fix:**
```
.panel { padding: 16px; }
.panel-header { 
  margin: 0; 
  padding: 0;  ← No double padding
}
```

---

## Skill-Based Refactoring (Automated)

### When to Use Skills

**Scenario 1: Refactoring existing surface**
```bash
# Surface has violations, needs cleanup

1. Run audit to understand what's wrong:
   npm run skill:usx-audit surfaces/workflow.css
   
2. System suggests repairs:
   → 5 hardcoded colors found
   → 12 hardcoded px padding found
   → 3 non-standard gaps found

3. Approve repairs:
   npm run skill:usx-color-reset surfaces/workflow.css
   npm run skill:usx-spacing-normalize surfaces/workflow.css
   npm run skill:usx-padding-isolation surfaces/workflow.css

4. Review output, test locally, commit
```

**Scenario 2: Audit before committing**
```bash
# Before pushing PR

npm run audit:usx-all
→ Shows conformance for all surfaces
→ Fails if any surface < 90%
→ If fail: choose repair skill or manual fix
```

**Scenario 3: Building new surface from scratch**
```bash
# Need new surface fast

npm run skill:usx-bootstrap-surface \
  --name my-new-surface \
  --components card panel button badge grid

→ Generates: surfaces/mynewsurface.css
→ With all standard component patterns
→ Ready to customize with surface-specific styles
```

---

## Quality Gates (CI/CD)

### Pre-commit (Local)
```bash
# Run before git commit
npm run audit:usx-style -- {modified files}

Criteria:
- No ✗ hardcoded colors
- No ✗ non-standard spacing
- Conformance >= 95%
```

### Pre-push (GitHub Actions)
```bash
# Run in CI on every push
npm run audit:usx-all

Criteria:
- All surfaces >= 90% conformance
- No regression from previous run
- Alert if any surface drops > 5%
```

### Pre-merge (PR Check)
```bash
# Reviewer confirms
- ✓ PR passes audit
- ✓ No layout shift (visual test)
- ✓ Follows component patterns
- ✓ Updated checklist complete
```

---

## Common Tasks by Role

### Frontend Developer
**New component in existing surface**
1. Copy component template from above
2. Customize colors/spacing using variables
3. Test locally: `npm run dev`
4. Audit: `npm run audit:usx-style -- {file}`
5. Commit with checklist ✓

**Bug fix in surface**
1. Make change to `.css` file
2. Use variables, not hardcoded values
3. Test to ensure no visual shift
4. Audit and commit

### Tech Lead (Code Review)
**Reviewing CSS changes**

Checklist:
- [ ] All `var(--pico-*)` for colors (with fallbacks)
- [ ] All `var(--usx-*)` for spacing
- [ ] No hardcoded px in padding/margin
- [ ] Standard component patterns used
- [ ] Audit result >= 95%
- [ ] Visual test: no layout shift
- [ ] PR description includes audit score

Reject if:
- ✗ Hardcoded colors without fallbacks
- ✗ Non-standard spacing values
- ✗ Audit < 90%
- ✗ Visual regression

### Maintenance/Refactoring Task
**Clean up old surface**
1. Run audit: identify violations
2. Use batch repair skills (color, spacing, padding)
3. Manual review of results
4. Visual regression test
5. Commit with "refactor: standardize {surface} styles"

---

## Resources & References

### Quick Links
- **Spacing Scale:** Check variables at `usx-spacing-scale.css`
- **Color Reset:** Check Pico mappings at `usx-pico-reset.css`
- **Component Patterns:** See templates above or `usx-spacing-scale.css`
- **Pico CSS Docs:** https://picocss.com/docs/css-variables
- **Full Roadmap:** `USX-STANDARDIZATION-ROADMAP.md`
- **Skills Strategy:** `USX-SKILLS-REFACTOR-STRATEGY.md`

### Variables Cheat Sheet
```
SPACING (use for padding/margin/gap):
  4px  → var(--usx-spacing-xs)
  8px  → var(--usx-spacing-sm)
  12px → var(--usx-spacing-md)
  16px → var(--usx-spacing-lg)
  24px → var(--usx-spacing-xl)
  32px → var(--usx-spacing-2xl)

COMPONENT SPECIFIC:
  Card padding:    var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal)
  Card gap:        var(--usx-card-gap)
  Button padding:  var(--usx-button-padding-vertical) var(--usx-button-padding-horizontal)
  Badge padding:   var(--usx-badge-padding-vertical) var(--usx-badge-padding-horizontal)
  Section padding: var(--usx-section-padding)
  Grid gap:        var(--usx-grid-gap)

COLORS (Pico tokens):
  Background:    var(--pico-background-color, #0d1117)
  Card BG:       var(--pico-card-background-color, #161b22)
  Card Section:  var(--pico-card-sectioning-background-color, #1c2128)
  Text:          var(--pico-color, #c9d1d9)
  Text muted:    var(--pico-muted-color, #8b949e)
  Border:        var(--pico-border-color, #30363d)
  Primary:       var(--pico-primary, #58a6ff)
  Primary hover: var(--pico-primary-hover, #3b82f6)
  Success:       var(--pico-ins-color, #3fb950)
  Error:         var(--pico-del-color, #f85149)
```

---

## FAQ

**Q: Can I use hardcoded px values?**  
A: Only in special cases with comments:
- Terminal font rendering (teletext)
- Scroll bar widths
- Border widths (1px ok)
- Other exceptional cases → add comment explaining why

**Q: What if design requires non-standard spacing?**  
A: 
1. Check if existing value works (might look good anyway)
2. If not, add new variable to `usx-spacing-scale.css`
3. Use new variable going forward
4. Document in PR why new value needed

**Q: Can I break standard component padding?**  
A: Only with strong reason + comment + code review approval

**Q: What happens if I don't use variables?**  
A: 
- Audit fails (< 95% conformance)
- PR can't merge (CI check fails)
- Future maintenance harder (harder to theme/update)

**Q: How do I know if my change is USX compliant?**  
A: Run: `npm run audit:usx-style -- {file}`  
Score >= 95% = compliant ✓

---

## Getting Help

### Stuck on style issue?
1. Check this guide's **Troubleshooting** section
2. Refer to **Component Reference** templates above
3. Review existing surface that works well
4. Ask in code review if unsure

### Need to refactor old surface?
1. See **Skill-Based Refactoring** section
2. Run audit first to understand violations
3. Use repair skills or manual fixes
4. Test visually before submitting

### Building new surface?
1. Use **skill_usx_bootstrap_surface** for instant template
2. Or copy patterns from **Component Reference**
3. You'll have conformant surface in minutes

---

## Summary

✅ **Do This:**
- Use `var(--usx-*)` for all spacing
- Use `var(--pico-*)` for all colors
- Follow component templates above
- Run audit before committing
- Test visually for layout shifts
- Document if breaking standards

❌ **Don't Do This:**
- Hardcoded hex colors
- Hardcoded px in padding/margin
- Non-standard spacing (2,3,5,6,7,9,10px)
- Nested div double-padding
- Inline styles instead of CSS
- Breaking standards without approval

---

**Questions?** See related docs or run: `npm run help:usx`
