/* ═══════════════════════════════════════════════════════════════════
   S101StoryBuilder — Story Builder (Dual-Mode)
   ═══════════════════════════════════════════════════════════════════
   Dual-mode: Typeform (linear steps) + Marp (slide deck).
   Renders raw content without USystemPage wrapper to avoid
   duplicate title divs when rendered inside the system shell.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useCallback } from 'react'
import { Icon } from '../components/Icon'
import TypeformRenderer, { type StoryStep } from './stories/components/TypeformRenderer'
import MarpSlideRenderer from './stories/components/MarpSlideRenderer'
import '../styles/system/story-forms.css'

type StoryMode = 'library' | 'typeform' | 'marp'

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

const SAMPLE_STORIES: StoryEntry[] = [
  {
    id: 'user-setup', title: 'User Setup Story', description: 'Configure your user profile — username, role, location, timezone, and UID.', stepCount: 5, mode: 'typeform', color: '#58a6ff', icon: 'person',
    steps: [
      { id: 'welcome', title: 'Welcome to uDos', description: 'Configure your $Variables.', type: 'info' },
      { id: 'username', title: 'Choose a Username', description: 'What should we call you?', type: 'collect', field: { key: 'username', label: 'Username', placeholder: 'Enter your username' } },
      { id: 'role', title: 'Your Role', description: 'What is your primary role?', type: 'select', field: { key: 'role', label: 'Role', options: [{ value: 'developer', label: 'Developer' }, { value: 'admin', label: 'Administrator' }] } },
      { id: 'location', title: 'Your Location', description: 'Where are you based?', type: 'collect', field: { key: 'location', label: 'Location', placeholder: 'e.g. Australia/Perth' } },
      { id: 'complete', title: 'Setup Complete!', description: 'Profile configured.', type: 'info' },
    ],
  },
  {
    id: 'workflow-intro', title: 'Workflow Orientation', description: 'A walkthrough of the workflow surface.', stepCount: 4, mode: 'marp', color: '#22c55e', icon: 'account_tree',
    steps: [
      { id: 's1', title: 'Workflow Surface', description: 'Your mission control center.', type: 'info' },
      { id: 's2', title: 'Mission Control', description: 'Monitor missions and health.', type: 'info' },
      { id: 's3', title: 'Tasks & Projects', description: 'Manage with Kanban boards.', type: 'info' },
      { id: 's4', title: 'Binder Compiler', description: 'Drop files to compile binders.', type: 'info' },
    ],
  },
  {
    id: 'system-admin', title: 'System Admin Guide', description: 'Overview of system pages, tools, secrets.', stepCount: 3, mode: 'marp', color: '#f0883e', icon: 'build',
    steps: [
      { id: 'a1', title: 'System Surface', description: 'Access /system.', type: 'info' },
      { id: 'a2', title: 'Secret Store', description: 'AES-256-GCM encrypted credentials.', type: 'info' },
      { id: 'a3', title: 'Variable Store', description: '$Variables across all surfaces.', type: 'info' },
    ],
  },
  {
    id: 'variables-demo', title: '$Variables Collection', description: 'Learn how $Variables work.', stepCount: 4, mode: 'typeform', color: '#a855f7', icon: 'tune',
    steps: [
      { id: 'v1', title: 'What are $Variables?', description: 'Named values stored centrally.', type: 'info' },
      { id: 'v2', title: 'Your Email', description: 'Bind to $email.', type: 'collect', field: { key: 'email', label: 'Email', placeholder: 'user@example.com' } },
      { id: 'v3', title: 'Unique ID', description: 'Auto-generated.', type: 'info' },
      { id: 'v4', title: 'All Set', description: 'Available as {{variable}}.', type: 'info' },
    ],
  },
]

export default function S101StoryBuilder() {
  const [mode, setMode] = useState<StoryMode>('library')
  const [activeStory, setActiveStory] = useState<StoryEntry | null>(null)
  const [completedValues, setCompletedValues] = useState<Record<string, string> | null>(null)

  const handlePlayTypeform = useCallback((story: StoryEntry) => {
    setActiveStory(story); setMode('typeform'); setCompletedValues(null)
  }, [])

  const handlePlayMarp = useCallback((story: StoryEntry) => {
    setActiveStory(story); setMode('marp'); setCompletedValues(null)
  }, [])

  const handleComplete = useCallback((values: Record<string, string>) => {
    setCompletedValues(values)
  }, [])

  const handleBack = useCallback(() => {
    setActiveStory(null); setMode('library'); setCompletedValues(null)
  }, [])

  return (
    <div className="story-builder">
      {mode === 'library' && (
        <>
          <div className="story-mode-toggle">
            <span>Available Stories</span>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px' }}>
              <span className="story-var-badge" style={{ '--story-accent': '#58a6ff' } as React.CSSProperties}>
                <Icon name="person" size={14} /> Typeform
              </span>
              <span className="story-var-badge" style={{ '--story-accent': '#22c55e' } as React.CSSProperties}>
                <Icon name="slideshow" size={14} /> Marp Slides
              </span>
              <span className="story-var-tag">$Variables</span>
            </div>
          </div>

          <div className="story-library">
            {SAMPLE_STORIES.map(story => (
              <div key={story.id} className="story-card">
                <div className="story-card-header">
                  <h3 className="story-card-title">{story.title}</h3>
                  <span className="story-card-badge" style={{ background: `${story.color}18`, color: story.color, border: `1px solid ${story.color}30` }}>
                    {story.mode === 'typeform' ? 'Form' : 'Slides'}
                  </span>
                </div>
                <p className="story-card-desc">{story.description}</p>
                <div className="story-card-meta"><span>{story.stepCount} steps</span></div>
                <div style={{ display: 'flex', gap: '6px', marginTop: '10px' }}>
                  {story.mode === 'typeform' ? (
                    <button className="story-step-btn story-step-btn--primary" onClick={() => handlePlayTypeform(story)} style={{ background: story.color, borderColor: story.color }}>
                      <Icon name="play_arrow" size={14} /> Play Form
                    </button>
                  ) : (
                    <button className="story-step-btn story-step-btn--primary" onClick={() => handlePlayMarp(story)} style={{ background: story.color, borderColor: story.color }}>
                      <Icon name="slideshow" size={14} /> View Slides
                    </button>
                  )}
                  <button className="story-step-btn" onClick={() => handlePlayTypeform(story)}>
                    <Icon name="edit" size={14} /> Edit
                  </button>
                </div>
              </div>
            ))}
          </div>

          {completedValues && Object.keys(completedValues).length > 0 && (
            <div className="sys-page-section" style={{ margin: '16px' }}>
              <div className="sys-page-section-header">
                <h3><Icon name="database" size={14} /> Last Collected Variables</h3>
                <span className="sys-page-section-badge">$Variables</span>
              </div>
              <div className="sys-page-variables-grid" style={{ padding: '12px' }}>
                {Object.entries(completedValues).map(([key, value]) => (
                  <div key={key} className="sys-var-card">
                    <div className="sys-var-card-icon" style={{ color: '#58a6ff' }}>
                      <Icon name="data_array" size={16} />
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
        </>
      )}

      {mode === 'typeform' && activeStory && (
        <>
          <div className="story-mode-toggle">
            <button className="story-step-btn" onClick={handleBack}><Icon name="arrow_back" size={14} /> Library</button>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span className="story-var-badge" style={{ '--story-accent': activeStory.color } as React.CSSProperties}>
                <Icon name="person" size={14} /> {activeStory.title}
              </span>
              <button className="story-step-btn" onClick={() => setMode('marp')}>
                <Icon name="slideshow" size={14} /> Switch to Slides
              </button>
            </div>
          </div>
          <TypeformRenderer
            story={{ storyId: activeStory.id, title: activeStory.title, steps: activeStory.steps }}
            onComplete={handleComplete}
            onCancel={handleBack}
            accentColor={activeStory.color}
          />
        </>
      )}

      {mode === 'marp' && activeStory && (
        <>
          <div className="story-mode-toggle">
            <button className="story-step-btn" onClick={handleBack}><Icon name="arrow_back" size={14} /> Library</button>
            <div style={{ marginLeft: 'auto', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <span className="story-var-badge" style={{ '--story-accent': activeStory.color } as React.CSSProperties}>
                <Icon name="slideshow" size={14} /> {activeStory.title}
              </span>
              {activeStory.steps.some(s => s.type === 'input' || s.type === 'collect' || s.type === 'select') && (
                <button className="story-step-btn" onClick={() => setMode('typeform')}>
                  <Icon name="person" size={14} /> Switch to Form
                </button>
              )}
            </div>
          </div>
          <MarpSlideRenderer
            steps={activeStory.steps}
            title={activeStory.title}
            accentColor={activeStory.color}
            onFinish={handleBack}
          />
        </>
      )}
    </div>
  )
}