/* ═══════════════════════════════════════════════════════════════════
   S101StoryBuilder — Story Builder System Page (Dual-Mode)
   ═══════════════════════════════════════════════════════════════════
   S101: Core — Story Builder
   Dual-mode: Typeform (linear steps) + Marp (slide deck).
   Features story library, editor, variable binding, and actions.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useCallback } from 'react'
import USystemPage from '../components/uSystemPage'
import { Icon } from '../components/Icon'
import TypeformRenderer, { type StoryStep, type StoryFormData } from './stories/components/TypeformRenderer'
import MarpSlideRenderer from './stories/components/MarpSlideRenderer'
import '../styles/system/story-forms.css'

type StoryMode = 'library' | 'typeform' | 'marp' | 'editor'

interface StoryEntry {
  id: string
  title: string
  description: string
  stepCount: number
  mode: 'typeform' | 'marp'
  color: string
  icon: string
  steps: StoryStep[]
}

// ─── Sample Stories ──────────────────────────────────────────────
const SAMPLE_STORIES: StoryEntry[] = [
  {
    id: 'user-setup',
    title: 'User Setup Story',
    description: 'Configure your user profile — username, role, location, timezone, and UID. Syncs to $Variables and Secret Store.',
    stepCount: 5,
    mode: 'typeform',
    color: '#58a6ff',
    icon: 'person',
    steps: [
      { id: 'welcome', title: 'Welcome to uDos', description: 'Let\'s set up your user profile. This will configure your $Variables and connect to the Secret Store.', type: 'info' },
      { id: 'username', title: 'Choose a Username', description: 'What should we call you? This will be used across the system.', type: 'collect', field: { key: 'username', label: 'Username', placeholder: 'Enter your username' } },
      { id: 'role', title: 'Your Role', description: 'What is your primary role?', type: 'select', field: { key: 'role', label: 'Role', options: [{ value: 'developer', label: 'Developer' }, { value: 'designer', label: 'Designer' }, { value: 'admin', label: 'Administrator' }, { value: 'user', label: 'User' }] } },
      { id: 'location', title: 'Your Location', description: 'Where are you based? This helps configure timezone and regional settings.', type: 'collect', field: { key: 'location', label: 'Location / Timezone', placeholder: 'e.g. Australia/Perth' } },
      { id: 'complete', title: 'Setup Complete!', description: 'Your profile has been configured. Your $Variables are synced to the system.', type: 'info' },
    ],
  },
  {
    id: 'workflow-intro',
    title: 'Workflow Orientation',
    description: 'A walkthrough of the workflow surface — missions, tasks, binder, and publish.',
    stepCount: 4,
    mode: 'marp',
    color: '#22c55e',
    icon: 'account_tree',
    steps: [
      { id: 'slide-1', title: 'Workflow Surface Overview', description: 'The Workflow Surface is your mission control center.', type: 'info' },
      { id: 'slide-2', title: 'Mission Control', description: 'Monitor active missions, workflow stats, and system health at a glance.', type: 'info' },
      { id: 'slide-3', title: 'Tasks & Projects', description: 'Manage tasks with Kanban boards and list views. Link them to missions.', type: 'info' },
      { id: 'slide-4', title: 'Binder Compiler', description: 'Drop files to compile binders. Process them into organized mission groups.', type: 'info' },
    ],
  },
  {
    id: 'system-admin',
    title: 'System Administration Guide',
    description: 'Overview of system pages, tools, secrets, and settings.',
    stepCount: 3,
    mode: 'marp',
    color: '#f0883e',
    icon: 'build',
    steps: [
      { id: 'sys-1', title: 'System Surface', description: 'Access all admin functions from /system — pages, tools, secrets, variables, settings.', type: 'info' },
      { id: 'sys-2', title: 'Secret Store', description: 'Manage API keys and credentials with AES-256-GCM encryption.', type: 'info' },
      { id: 'sys-3', title: 'Central Variable Store', description: 'User, installation, and secret $Variables available across all surfaces.', type: 'info' },
    ],
  },
  {
    id: 'variables-demo',
    title: '$Variables Collection',
    description: 'Learn how $Variables work across the system. Collect and bind values.',
    stepCount: 4,
    mode: 'typeform',
    color: '#a855f7',
    icon: 'tune',
    steps: [
      { id: 'var-1', title: 'What are $Variables?', description: '$Variables are named values stored centrally. They can be user-defined or system-generated.', type: 'info' },
      { id: 'var-2', title: 'Your Email', description: 'Enter your email address to bind to $email.', type: 'collect', field: { key: 'email', label: 'Email Address', placeholder: 'user@example.com' } },
      { id: 'var-3', title: 'Unique ID', description: 'Your system UID is automatically generated. You can view it in the Variables panel.', type: 'info' },
      { id: 'var-4', title: 'All Set', description: 'Variables are available as {{variable}} or $variable in templates, stories, and workflows.', type: 'info' },
    ],
  },
]

export default function S101StoryBuilder() {
  const [mode, setMode] = useState<StoryMode>('library')
  const [activeStory, setActiveStory] = useState<StoryEntry | null>(null)
  const [showTypeform, setShowTypeform] = useState(false)
  const [showMarp, setShowMarp] = useState(false)
  const [completedValues, setCompletedValues] = useState<Record<string, string> | null>(null)

  const handlePlayTypeform = useCallback((story: StoryEntry) => {
    setActiveStory(story)
    setShowTypeform(true)
    setShowMarp(false)
    setCompletedValues(null)
    setMode('typeform')
  }, [])

  const handlePlayMarp = useCallback((story: StoryEntry) => {
    setActiveStory(story)
    setShowMarp(true)
    setShowTypeform(false)
    setCompletedValues(null)
    setMode('marp')
  }, [])

  const handleTypeformComplete = useCallback((values: Record<string, string>) => {
    setCompletedValues(values)
    console.log('Story completed with values:', values)
  }, [])

  const handleMarpFinish = useCallback(() => {
    setShowMarp(false)
    setActiveStory(null)
    setMode('library')
  }, [])

  const handleCancel = useCallback(() => {
    setShowTypeform(false)
    setShowMarp(false)
    setActiveStory(null)
    setMode('library')
  }, [])

  const handleBackToLibrary = useCallback(() => {
    setShowTypeform(false)
    setShowMarp(false)
    setActiveStory(null)
    setCompletedValues(null)
    setMode('library')
  }, [])

  return (
    <USystemPage
      page={101}
      title="Story Builder"
      subtitle="Typeform-styled interactive forms & Marp-styled slideshows"
    >
      {/* Mode Toggle (when in library view) */}
      <div className="story-builder">
        {mode === 'library' && (
          <>
            {/* Story Library */}
            <div className="story-mode-toggle">
              <span style={{ fontSize: '12px', color: 'var(--pico-muted-color)', fontWeight: 500 }}>Available Stories</span>
              <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
                <span className="story-var-badge" style={{ '--story-accent': '#58a6ff' } as React.CSSProperties}>
                  <Icon name="person" size={12} /> Typeform
                </span>
                <span className="story-var-badge" style={{ '--story-accent': '#22c55e' } as React.CSSProperties}>
                  <Icon name="slideshow" size={12} /> Marp Slides
                </span>
                <span className="story-var-tag">$Variables</span>
              </div>
            </div>

            <div className="story-content">
              <div className="story-library">
                {SAMPLE_STORIES.map(story => (
                  <div key={story.id} className="story-card">
                    <div className="story-card-header">
                      <h3 className="story-card-title">{story.title}</h3>
                      <span
                        className="story-card-badge"
                        style={{
                          background: `${story.color}18`,
                          color: story.color,
                          border: `1px solid ${story.color}30`,
                        }}
                      >
                        {story.mode === 'typeform' ? 'Form' : 'Slides'}
                      </span>
                    </div>
                    <p className="story-card-desc">{story.description}</p>
                    <div className="story-card-meta">
                      <span>{story.stepCount} steps</span>
                    </div>
                    <div style={{ display: 'flex', gap: '6px', marginTop: '10px' }}>
                      {story.mode === 'typeform' ? (
                        <button
                          className="story-step-btn story-step-btn--primary"
                          onClick={() => handlePlayTypeform(story)}
                          style={{ background: story.color, borderColor: story.color, padding: '4px 12px', fontSize: '12px' }}
                        >
                          <Icon name="play_arrow" size={12} /> Play Form
                        </button>
                      ) : (
                        <button
                          className="story-step-btn story-step-btn--primary"
                          onClick={() => handlePlayMarp(story)}
                          style={{ background: story.color, borderColor: story.color, padding: '4px 12px', fontSize: '12px' }}
                        >
                          <Icon name="slideshow" size={12} /> View Slides
                        </button>
                      )}
                      <button
                        className="story-step-btn"
                        onClick={() => handlePlayTypeform(story)}
                        style={{ padding: '4px 12px', fontSize: '12px' }}
                      >
                        <Icon name="edit" size={12} /> Edit
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Collected values preview */}
              {completedValues && Object.keys(completedValues).length > 0 && (
                <div className="sys-page-section" style={{ marginTop: '16px' }}>
                  <div className="sys-page-section-header">
                    <h3><Icon name="database" size={14} /> Last Collected Variables</h3>
                    <span className="sys-page-section-badge">$Variables</span>
                  </div>
                  <div className="sys-page-variables-grid" style={{ padding: '12px' }}>
                    {Object.entries(completedValues).map(([key, value]) => (
                      <div key={key} className="sys-var-card">
                        <div className="sys-var-card-icon" style={{ color: '#58a6ff' }}>
                          <Icon name="variable" size={16} />
                        </div>
                        <div className="sys-var-card-info">
                          <div className="sys-var-card-label">{key}</div>
                          <div className="sys-var-card-value"><code>{value}</code></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </>
        )}

        {mode === 'typeform' && activeStory && (
          <div className="story-content">
            <div className="story-mode-toggle" style={{ borderTop: '1px solid var(--story-border)', marginTop: 0 }}>
              <button className="story-step-btn" onClick={handleBackToLibrary} style={{ padding: '4px 10px', fontSize: '12px' }}>
                <Icon name="arrow_back" size={12} /> Library
              </button>
              <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span className="story-var-badge" style={{ '--story-accent': activeStory.color } as React.CSSProperties}>
                  <Icon name="person" size={12} /> {activeStory.title}
                </span>
                <button className="story-step-btn" onClick={() => { setShowTypeform(false); setShowMarp(true); setMode('marp') }} style={{ padding: '4px 10px', fontSize: '12px' }}>
                  <Icon name="slideshow" size={12} /> Switch to Slides
                </button>
              </div>
            </div>
            <TypeformRenderer
              story={{ storyId: activeStory.id, title: activeStory.title, steps: activeStory.steps }}
              onComplete={handleTypeformComplete}
              onCancel={handleCancel}
              accentColor={activeStory.color}
            />
          </div>
        )}

        {mode === 'marp' && activeStory && (
          <div className="story-content">
            <div className="story-mode-toggle" style={{ borderTop: '1px solid var(--story-border)', marginTop: 0 }}>
              <button className="story-step-btn" onClick={handleBackToLibrary} style={{ padding: '4px 10px', fontSize: '12px' }}>
                <Icon name="arrow_back" size={12} /> Library
              </button>
              <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
                <span className="story-var-badge" style={{ '--story-accent': activeStory.color } as React.CSSProperties}>
                  <Icon name="slideshow" size={12} /> {activeStory.title}
                </span>
                {activeStory.steps.some(s => s.type === 'input' || s.type === 'collect' || s.type === 'select') && (
                  <button className="story-step-btn" onClick={() => { setShowMarp(false); setShowTypeform(true); setMode('typeform') }} style={{ padding: '4px 10px', fontSize: '12px' }}>
                    <Icon name="person" size={12} /> Switch to Form
                  </button>
                )}
              </div>
            </div>
            <MarpSlideRenderer
              steps={activeStory.steps}
              title={activeStory.title}
              accentColor={activeStory.color}
              onFinish={handleMarpFinish}
            />
          </div>
        )}
      </div>
    </USystemPage>
  )
}