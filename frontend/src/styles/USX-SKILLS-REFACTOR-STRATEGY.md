# USX Skills-Based Refactor Strategy
**Status:** Analysis Phase  
**Focus:** Skill-driven surface repair, rebuild, and fresh builds  
**Date:** 2026-06-24

---

## Executive Summary

The USX standardization can be accelerated and automated using skills-based refactoring:

1. **Detection Skill** – Scan surfaces, identify non-conformant styles
2. **Repair Skill** – Automatically replace hardcoded values with variables
3. **Rebuild Skill** – Reconstruct complex surfaces from scratch using standards
4. **New Surface Skill** – Build fresh surfaces that conform to USX standards from day one

This document maps the refactoring work to backend skills for automation and validation.

---

## Part 1: Style Analysis & Detection

### 1.1 USX Style Audit Skill

**Purpose:** Detect style violations across surfaces  
**Input:** CSS file paths to audit  
**Output:** Report of violations + recommendations

**Violations to detect:**
```
✗ Hardcoded hex colors (not using var(--pico-*))
✗ Raw px padding/margin (not using var(--usx-*))
✗ Inconsistent component padding (not 14/16px standard)
✗ Non-standard gaps (using values outside 4,8,12,16,24px)
✗ Nested div double-padding patterns
✗ Missing Pico variables for colors
✗ Inline style attributes (should be CSS classes)
✗ Hardcoded font sizes (not from Pico)
```

**Implementation approach:**
- Create skill: `skill_usx_style_audit.py`
- Regex-scan CSS for violations
- Generate structured violations list
- Map violations to fix strategies

### 1.2 Surface Conformance Check

**Surfaces to check:**
| Surface | File | Priority | Risk |
|---------|------|----------|------|
| UIHub | `hub/dashboard.css` | HIGH | Medium |
| Workflow | `surfaces/workflow.css` | HIGH | Low |
| Developer | `surfaces/developer.css` | HIGH | High |
| uServer | `userver.css` | MED | Low |
| uCode | `surfaces/ucode.css` | HIGH | Medium |
| System | `surfaces/system.css` (if exists) | MED | Unknown |

**Audit Results Template:**
```json
{
  "surface": "workflow",
  "file": "surfaces/workflow.css",
  "violations": [
    {
      "type": "hardcoded_color",
      "line": 42,
      "pattern": "#161b22",
      "suggested_fix": "var(--pico-card-background-color)",
      "count": 5
    },
    {
      "type": "hardcoded_padding",
      "line": 59,
      "pattern": "14px 16px",
      "suggested_fix": "var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal)",
      "count": 12
    },
    {
      "type": "non_standard_gap",
      "line": 78,
      "pattern": "gap: 10px",
      "suggested_fix": "var(--usx-spacing-sm)",
      "count": 3
    }
  ],
  "conformance_score": 0.65,
  "estimated_fix_time_minutes": 25
}
```

---

## Part 2: Automated Repair Skills

### 2.1 Color Reset Skill

**Purpose:** Replace hardcoded hex colors with Pico variables  
**Input:** CSS file + color mapping  
**Output:** Updated CSS with variables

**Mappings:**
```
#0d1117 → var(--pico-background-color, #0d1117)
#161b22 → var(--pico-card-background-color, #161b22)
#1c2128 → var(--pico-card-sectioning-background-color, #1c2128)
#c9d1d9 → var(--pico-color, #c9d1d9)
#8b949e → var(--pico-muted-color, #8b949e)
#30363d → var(--pico-border-color, #30363d)
#58a6ff → var(--pico-primary, #58a6ff)
#3b82f6 → var(--pico-primary-hover, #3b82f6)
#3fb950 → var(--pico-ins-color, #3fb950)
#f85149 → var(--pico-del-color, #f85149)
#d29922 → Fallback case (warning color)
```

**Skill:** `skill_usx_color_reset.py`
- Input: CSS file path
- Parse all color values
- Replace hex with var() + fallback
- Preserve existing var() usage
- Output: Fixed CSS

### 2.2 Spacing Normalization Skill

**Purpose:** Replace hardcoded px padding/margin/gap with variables  
**Input:** CSS file + spacing rules  
**Output:** Updated CSS with spacing variables

**Mapping logic:**
```
padding/margin/gap values:
  2px → var(--usx-spacing-xs) [if contexts allow]
  4px → var(--usx-spacing-xs)
  6px → var(--usx-spacing-xs) or var(--usx-compact-gap)
  8px → var(--usx-spacing-sm)
  10px → var(--usx-spacing-sm) [round down]
  12px → var(--usx-spacing-md)
  14px → var(--usx-card-padding-vertical) [if padding context]
  16px → var(--usx-spacing-lg)
  20px → var(--usx-spacing-lg) or var(--usx-section-separator)
  24px → var(--usx-spacing-xl)
  28px, 32px → var(--usx-spacing-2xl)
```

**Context-aware replacement:**
- If `.card` or `card-*` class: use card variables
- If `.section` or `section-*` class: use section variables
- If `gap` CSS property: use gap variables
- If `padding` on large container: use `--usx-section-padding`

**Skill:** `skill_usx_spacing_normalize.py`
- Input: CSS file path
- Detect context of each px value
- Replace with appropriate variable
- Preserve intentional special cases
- Output: Fixed CSS with comments on special cases

### 2.3 Double-Padding Fix Skill

**Purpose:** Detect and fix nested div padding accumulation  
**Input:** CSS file + HTML structure hints  
**Output:** Updated CSS with proper padding isolation

**Pattern detection:**
```css
/* BROKEN PATTERN */
.panel { padding: 16px; }
.panel-header { padding: 4px; }  ← Causes double space
.panel-content { padding: 8px; } ← More stacking

/* FIXED PATTERN */
.panel { padding: 16px; }
.panel-header { margin: 0; padding: 0; } ← No double space
.panel-content { margin: 0; padding: 0; } ← Inherits panel padding
```

**Skill:** `skill_usx_padding_isolation.py`
- Input: CSS file
- Detect panel/section nesting patterns
- Find unnecessary padding on child elements
- Replace with `margin: 0; padding: 0;`
- Preserve intentional margins (e.g., `margin-bottom` for spacing)
- Output: Fixed CSS

---

## Part 3: Surface Rebuild Skills

### 3.1 Surface Audit & Rebuild Assessment

**Purpose:** Evaluate if surface should be patched or rebuilt  
**Decision matrix:**

| Condition | Violations | Complexity | Decision |
|-----------|-----------|-----------|----------|
| Few violations (<5) | <10% fail | Low | **PATCH** |
| Moderate violations (5-20) | 10-30% fail | Medium | **PATCH** |
| Many violations (>20) | >30% fail | High | **REBUILD** |
| Unknown/Complex structure | Any | Unknown | **ANALYZE** then decide |

**Risk assessment:**
- `ucode.css`: Moderate → PATCH (fix colors first)
- `hub/dashboard.css`: Moderate → PATCH (fix padding)
- `developer.css`: Many → Consider REBUILD vs PATCH
- `workflow.css`: Moderate → PATCH
- `userver.css`: Few → PATCH

### 3.2 Rebuild Skill (Complex Surfaces)

**Purpose:** Reconstruct surface CSS from scratch using standards  
**Input:** Existing surface CSS + design requirements  
**Output:** New standards-compliant CSS

**Rebuild process:**
1. Analyze existing surface structure (components, hierarchy)
2. Extract unique styles vs. template violations
3. Build new CSS from scratch using standardized patterns
4. Validate against existing visual design
5. Generate mapping from old classes → new classes

**Example: `developer.css` rebuild**

Old patterns to extract:
```
- Floating panels (chat, preview)
- Tab bar with active states
- Code editor styling
- Loading animations
- Status badges
- Chat message bubbles
```

Rebuild from standards:
```css
/* Use standard component patterns */
.developer-preview-panel {
  padding: var(--usx-section-padding);
  background: var(--pico-card-background-color);
  gap: var(--usx-section-gap);
}

.developer-tab-btn {
  padding: var(--usx-button-padding-vertical) var(--usx-button-padding-horizontal);
  border-radius: 6px;
}
```

**Skill:** `skill_usx_surface_rebuild.py`
- Input: Old surface CSS file
- Extract meaningful patterns
- Generate new CSS using standards
- Map old classes to new structure
- Output: New CSS + migration guide

---

## Part 4: New Surface Bootstrap Skill

### 4.1 Fresh Surface Template

**Purpose:** Generate new surface CSS that conforms to standards from day one  
**Input:** Surface name + component list  
**Output:** Ready-to-use CSS template

**Template structure:**
```css
/* Generated: 2026-06-24 */
/* Surface: {surface_name} */
/* Components: {list} */

.{surface}-surface {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--pico-background-color);
  color: var(--pico-color);
}

.{surface}-panel {
  padding: var(--usx-section-padding);
  display: flex;
  flex-direction: column;
  gap: var(--usx-section-gap);
  background: var(--pico-card-background-color);
  border: 1px solid var(--pico-border-color);
  border-radius: 8px;
}

.{surface}-card {
  padding: var(--usx-card-padding-vertical) var(--usx-card-padding-horizontal);
  display: flex;
  flex-direction: column;
  gap: var(--usx-card-gap);
  background: var(--pico-card-background-color);
  border: 1px solid var(--pico-border-color);
  border-radius: 8px;
}

.{surface}-button {
  padding: var(--usx-button-padding-vertical) var(--usx-button-padding-horizontal);
  border: 1px solid var(--pico-border-color);
  background: var(--pico-card-background-color);
  color: var(--pico-color);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.{surface}-button:hover {
  border-color: var(--pico-primary);
  background: rgba(88, 166, 255, 0.08);
}

.{surface}-badge {
  padding: var(--usx-badge-padding-vertical) var(--usx-badge-padding-horizontal);
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  background: var(--pico-card-sectioning-background-color);
  color: var(--pico-muted-color);
  font-size: 0.875rem;
  white-space: nowrap;
}

/* Surface-specific grid */
.{surface}-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--usx-grid-gap);
}

/* Surface-specific responsive */
@media (max-width: 1024px) {
  .{surface}-grid {
    grid-template-columns: 1fr;
  }
}
```

**Skill:** `skill_usx_bootstrap_surface.py`
- Input: Surface name, component requirements
- Generate template using standard patterns
- Create HTML/JSX example
- Output: Ready CSS + component examples

---

## Part 5: Developer Workflow Integration

### 5.1 Refactor Checklist (Skill-Driven)

**For each surface (in priority order):**

```yaml
Surface: ucode.css
Priority: HIGH
Status: PATCH CANDIDATE
Steps:
  1. Run audit: skill_usx_style_audit → report
  2. Backup original file
  3. Run color reset: skill_usx_color_reset → fixed
  4. Run spacing normalize: skill_usx_spacing_normalize → fixed
  5. Run padding isolation: skill_usx_padding_isolation → fixed
  6. Manual review of special cases
  7. Test visually in browser
  8. Compare layout with original (should be identical)
  9. Commit with clear message
  10. Next: hub/dashboard.css
```

### 5.2 CI/CD Integration Points

**For every surface CSS change:**

```bash
# Pre-commit
npm run audit:usx-style -- surfaces/workflow.css
# → Should report conformance score ≥ 95%

# Post-merge (in CI)
npm run audit:usx-all
# → Generate conformance report for all surfaces
# → Fail if any surface < 90%
```

---

## Part 6: Skills Implementation Tasks

### Phase 6.1: Create Audit Skill
```python
# backend/app/skills/skill_usx_audit.py
class SkillUSXAudit:
    """Scan CSS files for USX violations"""
    
    def execute(self, css_file_path: str) -> USXAuditReport:
        """Analyze CSS file"""
        # Scan for violations
        # Return structured report
```

**Triggers:**
- Manual: `POST /api/skills/usx-audit?file=surfaces/workflow.css`
- CI: On PR for any `*.css` changes
- Scheduled: Daily scan of all surfaces

### Phase 6.2: Create Repair Skills
```python
# backend/app/skills/skill_usx_color_reset.py
class SkillUSXColorReset:
    """Automatically replace hardcoded colors"""

# backend/app/skills/skill_usx_spacing_normalize.py
class SkillUSXSpacingNormalize:
    """Normalize hardcoded px to variables"""

# backend/app/skills/skill_usx_padding_isolation.py
class SkillUSXPaddingIsolation:
    """Fix nested div double-padding"""
```

**Workflow:**
1. Audit → identify violations
2. User reviews suggestions
3. Approve repair skill
4. Skills run in sequence
5. Review results, test locally
6. Commit if passing

### Phase 6.3: Create Rebuild Skill
```python
# backend/app/skills/skill_usx_rebuild_surface.py
class SkillUSXRebuildSurface:
    """Reconstruct surface from scratch"""
    
    def execute(self, surface_name: str, analysis_report: dict):
        """Rebuild surface CSS"""
        # Extract meaningful patterns
        # Generate new CSS
        # Return new CSS + migration map
```

### Phase 6.4: Create Bootstrap Skill
```python
# backend/app/skills/skill_usx_bootstrap_surface.py
class SkillUSXBootstrapSurface:
    """Generate new standards-compliant surface"""
    
    def execute(self, surface_name: str, components: List[str]):
        """Create new surface CSS template"""
        # Generate template
        # Create examples
        # Return ready-to-use CSS
```

---

## Part 7: Estimated Effort (Skill-Accelerated)

### Without Skills (Manual)
| Surface | Manual Work | Risk |
|---------|-------------|------|
| ucode.css | 45 min | Medium |
| hub/dashboard.css | 30 min | Low |
| workflow.css | 25 min | Low |
| developer.css | 60 min | High |
| userver.css | 20 min | Low |
| **Total** | **180 min (3 hrs)** | **Medium** |

### With Skills (Automated)
| Phase | Work | Automation Savings |
|-------|------|-------------------|
| 6.1-4: Skill dev | 8 hours | One-time investment |
| Audit all surfaces | 5 min | 90% faster |
| Fix ucode.css | 10 min | 75% faster |
| Fix hub/dashboard.css | 8 min | 73% faster |
| Fix workflow.css | 7 min | 72% faster |
| Verify developer.css | 15 min | Analyze if rebuild needed |
| Fix userver.css | 6 min | 70% faster |
| **Phase 2 Total** | **~1 hour** | **80% time saved** |
| **Next 3 surfaces** | **~1 hour** | **80% time saved** |

---

## Part 8: Success Criteria (Skill-Based)

### Short Term (Phase 2)
- [ ] All audit skills working
- [ ] ucode.css repairs validated
- [ ] hub/dashboard.css standardized
- [ ] Conformance score ≥ 95% for all patched surfaces
- [ ] Visual regression tests: PASS
- [ ] No layout shift from originals

### Medium Term (Phase 3)
- [ ] All repair skills operational
- [ ] All surfaces at 95%+ conformance
- [ ] New surfaces bootstrap in < 5 minutes
- [ ] CI/CD integration: conformance checks on every PR

### Long Term (Phase 4+)
- [ ] Rebuild skill proven on developer.css
- [ ] All new surfaces use standards (100%)
- [ ] Legacy surfaces migrated or deprecated
- [ ] Skills library documented for team

---

## Related Resources

- **Standardization Roadmap:** `USX-STANDARDIZATION-ROADMAP.md`
- **Analysis:** `USX-STANDARDIZATION-ANALYSIS.md`
- **Import Order:** `usx-import-order.md`
- **Spacing Scale:** `usx-spacing-scale.css`
- **Reset Rules:** `usx-pico-reset.css`

---

## Next Actions

1. **Create audit skill** (`skill_usx_audit.py`) - validates approach
2. **Run audit on all surfaces** - baseline measurements
3. **Create color reset skill** - simplest automation
4. **Test color reset on ucode.css** - proof of concept
5. **Expand to spacing skill** - larger impact
6. **Integrate to CI/CD** - enforce standards going forward
