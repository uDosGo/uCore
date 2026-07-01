/* ═══════════════════════════════════════════════════════════════════
   TypeformRenderer — Linear step-by-step form renderer
   Renders story steps as Typeform-style cards with progress indicators,
   variable binding, and navigation.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useCallback } from 'react'
import { Icon } from '../../../components/Icon'

export interface StoryStep {
  id: string
  title: string
  description?: string
  type: 'input' | 'select' | 'info' | 'collect'
  field?: {
    key: string
    label: string
    placeholder?: string
    options?: { value: string; label: string }[]
  }
}

export interface StoryFormData {
  storyId: string
  title: string
  steps: StoryStep[]
}

interface TypeformRendererProps {
  story: StoryFormData
  initialValues?: Record<string, string>
  onComplete: (values: Record<string, string>) => void
  onCancel?: () => void
  accentColor?: string
}

export default function TypeformRenderer({
  story,
  initialValues = {},
  onComplete,
  onCancel,
  accentColor = '#58a6ff',
}: TypeformRendererProps) {
  const [currentStep, setCurrentStep] = useState(0)
  const [values, setValues] = useState<Record<string, string>>(initialValues)
  const [completed, setCompleted] = useState(false)

  const totalSteps = story.steps.length
  const step = story.steps[currentStep]

  const handleNext = useCallback(() => {
    if (currentStep < totalSteps - 1) {
      setCurrentStep(prev => prev + 1)
    } else {
      setCompleted(true)
      onComplete(values)
    }
  }, [currentStep, totalSteps, onComplete, values])

  const handleBack = useCallback(() => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1)
    }
  }, [currentStep])

  const handleValueChange = useCallback((key: string, value: string) => {
    setValues(prev => ({ ...prev, [key]: value }))
  }, [])

  const progressPercent = ((currentStep + 1) / totalSteps) * 100

  if (completed) {
    return (
      <div className="story-typeform">
        <div className="story-step-card" style={{ textAlign: 'center', padding: '40px' }}>
          <div style={{ marginBottom: '16px' }}>
            <Icon name="check_circle" size={48} style={{ color: accentColor }} />
          </div>
          <h2 className="story-step-title" style={{ fontSize: '24px' }}>Complete!</h2>
          <p className="story-step-desc">
            All steps completed. Your responses have been collected.
          </p>
          <div className="story-step-nav" style={{ justifyContent: 'center' }}>
            <button
              className="story-step-btn story-step-btn--primary"
              onClick={() => { setCurrentStep(0); setCompleted(false); setValues({}) }}
              style={{ '--story-accent': accentColor } as React.CSSProperties}
            >
              <Icon name="refresh" size={14} /> Start Over
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="story-typeform">
      {/* Progress Bar */}
      <div className="story-progress">
        {story.steps.map((s, idx) => (
          <React.Fragment key={s.id}>
            <div
              className={`story-progress-step ${
                idx === currentStep ? 'story-progress-step--active' :
                idx < currentStep ? 'story-progress-step--done' : ''
              }`}
              style={idx === currentStep ? { background: accentColor, boxShadow: `0 0 6px ${accentColor}` } : {}}
            />
            {idx < totalSteps - 1 && (
              <div className={`story-progress-line ${idx < currentStep ? 'story-progress-line--done' : ''}`}
                style={idx < currentStep ? { background: accentColor } : {}}
              />
            )}
          </React.Fragment>
        ))}
        <span className="story-step-counter">{currentStep + 1} / {totalSteps}</span>
      </div>

      {/* Step Card */}
      <div className="story-step-card" key={step.id} style={{ '--story-accent': accentColor } as React.CSSProperties}>
        <h2 className="story-step-title">{step.title}</h2>
        {step.description && <p className="story-step-desc">{step.description}</p>}

        {step.type === 'info' && (
          <div className="story-step-input-group">
            <p style={{ fontSize: '14px', color: 'var(--story-text)', lineHeight: '1.6' }}>
              {step.description}
            </p>
          </div>
        )}

        {step.type === 'input' && step.field && (
          <div className="story-step-input-group">
            <div className="story-step-field">
              <label className="story-step-label">{step.field.label}</label>
              <input
                className="story-step-input"
                type="text"
                placeholder={step.field.placeholder || ''}
                value={values[step.field.key] || ''}
                onChange={e => handleValueChange(step.field!.key, e.target.value)}
                autoFocus
              />
            </div>
          </div>
        )}

        {step.type === 'select' && step.field?.options && (
          <div className="story-step-input-group">
            <div className="story-step-field">
              <label className="story-step-label">{step.field.label}</label>
              <select
                className="story-step-select"
                value={values[step.field.key] || ''}
                onChange={e => handleValueChange(step.field!.key, e.target.value)}
              >
                <option value="">Select...</option>
                {step.field.options.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {step.type === 'collect' && (
          <div className="story-step-input-group">
            <div className="story-var-badge" style={{ '--story-accent': accentColor } as React.CSSProperties}>
              <Icon name="database" size={12} />
              Collecting: ${step.field?.key || 'variable'}
            </div>
            {step.field && (
              <div className="story-step-field">
                <label className="story-step-label">{step.field.label}</label>
                <input
                  className="story-step-input"
                  type="text"
                  placeholder={step.field.placeholder || 'Enter value'}
                  value={values[step.field.key] || ''}
                  onChange={e => handleValueChange(step.field!.key, e.target.value)}
                  autoFocus
                />
              </div>
            )}
          </div>
        )}

        {/* Navigation */}
        <div className="story-step-nav">
          <div>
            {currentStep > 0 && (
              <button className="story-step-btn" onClick={handleBack}>
                <Icon name="chevron_left" size={14} /> Back
              </button>
            )}
            {onCancel && currentStep === 0 && (
              <button className="story-step-btn" onClick={onCancel} style={{ marginLeft: 8 }}>
                Cancel
              </button>
            )}
          </div>
          <button
            className="story-step-btn story-step-btn--primary"
            onClick={handleNext}
            style={{ background: accentColor, borderColor: accentColor }}
          >
            {currentStep < totalSteps - 1 ? (
              <>Next <Icon name="chevron_right" size={14} /></>
            ) : (
              <>Complete <Icon name="check" size={14} /></>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}