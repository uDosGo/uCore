/* ═══════════════════════════════════════════════════════════════════
   MarpSlideRenderer — Slide deck renderer inspired by Marp
   Renders story steps as presentation-style slides with navigation.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useCallback } from 'react'
import { Icon } from '../../../components/Icon'
import type { StoryStep } from './TypeformRenderer'

interface MarpSlideRendererProps {
  steps: StoryStep[]
  title: string
  accentColor?: string
  onFinish?: () => void
}

export default function MarpSlideRenderer({
  steps,
  title,
  accentColor = '#58a6ff',
  onFinish,
}: MarpSlideRendererProps) {
  const [currentSlide, setCurrentSlide] = useState(0)
  const totalSlides = steps.length

  const slide = steps[currentSlide]

  const goNext = useCallback(() => {
    if (currentSlide < totalSlides - 1) {
      setCurrentSlide(prev => prev + 1)
    } else if (onFinish) {
      onFinish()
    }
  }, [currentSlide, totalSlides, onFinish])

  const goPrev = useCallback(() => {
    if (currentSlide > 0) {
      setCurrentSlide(prev => prev - 1)
    }
  }, [currentSlide])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
      e.preventDefault()
      goNext()
    } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
      e.preventDefault()
      goPrev()
    }
  }, [goNext, goPrev])

  if (!slide) {
    return (
      <div className="story-marp">
        <div className="story-slide" style={{ textAlign: 'center', justifyContent: 'center' }}>
          <h2 className="story-slide-header" style={{ color: accentColor }}>End of Presentation</h2>
          <p className="story-slide-subtitle">No more slides.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="story-marp" onKeyDown={handleKeyDown} tabIndex={0}>
      {/* Slide */}
      <div
        className="story-slide"
        style={{ '--story-accent': accentColor } as React.CSSProperties}
      >
        <div className="story-slide-header" style={{ color: accentColor }}>
          {slide.title}
        </div>
        {slide.description && (
          <div className="story-slide-subtitle">{slide.description}</div>
        )}
        <div className="story-slide-body">
          {slide.type === 'info' && (
            <div style={{ fontSize: '16px', lineHeight: '1.7' }}>
              {slide.description}
            </div>
          )}
          {slide.type === 'input' && slide.field && (
            <div>
              <p style={{ marginBottom: '8px', fontWeight: 500 }}>{slide.field.label}</p>
              <div className="story-var-badge" style={{ '--story-accent': accentColor } as React.CSSProperties}>
                <Icon name="edit" size={12} />
                ${slide.field.key}
              </div>
            </div>
          )}
          {slide.type === 'collect' && slide.field && (
            <div>
              <p style={{ marginBottom: '8px', fontWeight: 500 }}>
                <span className="story-var-tag">$Variable</span> {slide.field.label}
              </p>
              <div className="story-var-badge" style={{ '--story-accent': accentColor } as React.CSSProperties}>
                <Icon name="database" size={12} />
                Collect: ${slide.field.key}
              </div>
            </div>
          )}
          {slide.type === 'select' && slide.field?.options && (
            <div>
              <p style={{ marginBottom: '8px', fontWeight: 500 }}>{slide.field.label}</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {slide.field.options.map(opt => (
                  <div
                    key={opt.value}
                    style={{
                      padding: '10px 14px',
                      border: '1px solid var(--story-border)',
                      borderRadius: '6px',
                      fontSize: '14px',
                    }}
                  >
                    {opt.label}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="story-slide-footer">
          {title} · {currentSlide + 1} / {totalSlides}
        </div>
      </div>

      {/* Navigation */}
      <div className="story-slide-nav">
        <button
          className="story-slide-btn"
          onClick={goPrev}
          disabled={currentSlide === 0}
        >
          <Icon name="chevron_left" size={14} /> Previous
        </button>
        <span className="story-slide-counter">{currentSlide + 1} / {totalSlides}</span>
        <button
          className="story-slide-btn"
          onClick={goNext}
          style={currentSlide === totalSlides - 1 ? { borderColor: accentColor, color: accentColor } : {}}
        >
          {currentSlide < totalSlides - 1 ? (
            <>Next <Icon name="chevron_right" size={14} /></>
          ) : (
            <>Finish <Icon name="check" size={14} /></>
          )}
        </button>
      </div>
    </div>
  )
}