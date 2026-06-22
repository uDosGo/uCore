/* ═══════════════════════════════════════════════════════════════════
   DocumentationSurface — Learning Hub & Documentation
   ═══════════════════════════════════════════════════════════════════
   First-class surface for S600 Learning Hub — tutorials, guides,
   educational resources, and Jekyll-based documentation site.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState } from 'react'
import { GlobalToolbar } from '../../components/GlobalToolbar'
import { Icon } from '../../components/Icon'
import '../../styles/hub/index.css'

type DocumentationTab = 'learning' | 'guide' | 'api'

const DOCUMENTATION_TABS = [
  { id: 'learning', icon: 'school', label: 'Learning Hub' },
  { id: 'guide', icon: 'menu_book', label: 'Guide & Docs' },
  { id: 'api', icon: 'code', label: 'API Reference' },
]

export default function DocumentationSurface() {
  const [activeTab, setActiveTab] = useState<DocumentationTab>('learning')
  
  const docsUrl = 'file:///Users/fredbook/Public/doc-sites/DevStudio-docs/_site/index.html'
  const guideUrl = 'file:///Users/fredbook/Public/doc-sites/DevStudio-docs/_site/guide/index.html'

  const toolbar = {
    tabs: DOCUMENTATION_TABS.map(t => ({
      id: t.id,
      icon: t.icon,
      label: t.label,
      active: t.id === activeTab,
      onClick: () => setActiveTab(t.id as DocumentationTab),
    })),
  }

  return (
    <div className="usx-surface" style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: 'var(--pico-card-background-color, #0d1117)' }}>
      <GlobalToolbar tabs={toolbar.tabs} />

      <main className="usx-surface-main" style={{ flex: 1, overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
        {activeTab === 'learning' && (
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: '24px', gap: '24px' }}>
            <div>
              <h1 style={{ margin: '0 0 8px 0', fontSize: '32px', fontWeight: 700 }}>📚 Learning Hub</h1>
              <p style={{ margin: 0, fontSize: '16px', color: 'var(--pico-muted-color, #8b949e)' }}>
                Tutorials, guides, courses, and skill tracking for mastering uCore
              </p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
              <article style={{ padding: '16px', border: '1px solid var(--pico-form-element-border-color, #30363d)', borderRadius: '8px', background: 'var(--pico-form-element-background-color, #0d1117)' }}>
                <header style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Icon name="school" size={24} style={{ color: '#a371f7' }} />
                  <strong style={{ fontSize: '16px' }}>Course Library</strong>
                </header>
                <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--pico-muted-color, #8b949e)' }}>
                  Browse available courses, tutorials, and learning paths.
                </p>
                <button style={{ padding: '8px 16px', background: '#a371f7', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px', fontWeight: 500 }}>
                  Browse Courses
                </button>
              </article>

              <article style={{ padding: '16px', border: '1px solid var(--pico-form-element-border-color, #30363d)', borderRadius: '8px', background: 'var(--pico-form-element-background-color, #0d1117)' }}>
                <header style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Icon name="emoji_events" size={24} style={{ color: '#fbbf24' }} />
                  <strong style={{ fontSize: '16px' }}>Achievements</strong>
                </header>
                <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--pico-muted-color, #8b949e)' }}>
                  View earned badges, certificates, and milestones.
                </p>
                <button style={{ padding: '8px 16px', background: '#fbbf24', color: '#0d1117', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px', fontWeight: 500 }}>
                  View Achievements
                </button>
              </article>

              <article style={{ padding: '16px', border: '1px solid var(--pico-form-element-border-color, #30363d)', borderRadius: '8px', background: 'var(--pico-form-element-background-color, #0d1117)' }}>
                <header style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                  <Icon name="assessment" size={24} style={{ color: '#34d399' }} />
                  <strong style={{ fontSize: '16px' }}>Skill Tracker</strong>
                </header>
                <p style={{ margin: '0 0 12px 0', fontSize: '14px', color: 'var(--pico-muted-color, #8b949e)' }}>
                  Track your progress across skills and competencies.
                </p>
                <button style={{ padding: '8px 16px', background: '#34d399', color: '#0d1117', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '14px', fontWeight: 500 }}>
                  Track Skills
                </button>
              </article>
            </div>
          </div>
        )}

        {activeTab === 'guide' && (
          <iframe
            src={guideUrl}
            style={{
              flex: 1,
              border: 'none',
              width: '100%',
              height: '100%',
            }}
            title="uCore Documentation Guide"
          />
        )}

        {activeTab === 'api' && (
          <iframe
            src={docsUrl}
            style={{
              flex: 1,
              border: 'none',
              width: '100%',
              height: '100%',
            }}
            title="uCore API Reference"
          />
        )}
      </main>

      <footer style={{ padding: '12px 24px', fontSize: '12px', color: 'var(--pico-muted-color, #8b949e)', borderTop: '1px solid var(--pico-form-element-border-color, #30363d)' }}>
        <span>🎓 Learning Hub · Jekyll Documentation · uCore Knowledge Base</span>
      </footer>
    </div>
  )
}
