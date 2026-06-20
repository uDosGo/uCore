/* ═══════════════════════════════════════════════════════════════════
   EditorView — Markdown editor with live preview, bob autocomplete,
   and publish support. Modular component for use in any surface.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react'
import { Icon } from './Icon'
import { InlineBob } from '../surfaces/proseui/components/InlineBob'
import type { BobStyle, BobSize } from '../surfaces/proseui/components/InlineBob'
import { renderMarkdown } from '../utils/renderMarkdown'

// ─── Bob shortcode regex ────────────────────────────────────────
const BOB_SHORTCODE_RE = /:bob:([a-z0-9_-]+)(?::(16x16|32x32))?(?::(mono_chrome|teletext|full_color))?:/gi

function parseBobShortcode(match: RegExpExecArray): { name: string; size: BobSize; style: BobStyle } {
  const name = match[1]
  const size = (match[2] as BobSize) || '16x16'
  const style = (match[3] as BobStyle) || 'mono_chrome'
  return { name, size, style }
}

// ─── Markdown Preview Component (with bob shortcode rendering) ──
const MarkdownPreview: React.FC<{ content: string }> = ({ content }) => {
  const parts: React.ReactNode[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null = null
  const re = new RegExp(BOB_SHORTCODE_RE.source, 'gi')

  while ((match = re.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const textBefore = content.slice(lastIndex, match.index)
      parts.push(
        <span key={`text-${lastIndex}`} dangerouslySetInnerHTML={{ __html: renderMarkdown(textBefore) }} />
      )
    }
    const parsed = parseBobShortcode(match)
    parts.push(
      <InlineBob key={`bob-${match.index}`} prompt={parsed.name} style={parsed.style} size={parsed.size} />
    )
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < content.length) {
    const textAfter = content.slice(lastIndex)
    parts.push(
      <span key={`text-${lastIndex}`} dangerouslySetInnerHTML={{ __html: renderMarkdown(textAfter) }} />
    )
  }

  if (parts.length === 0) {
    return <div className="editor-preview" dangerouslySetInnerHTML={{ __html: renderMarkdown(content) }} />
  }

  return <div className="editor-preview">{parts}</div>
}

// ─── Bob Picker Modal ───────────────────────────────────────────
interface BobPickerModalProps {
  onInsert: (prompt: string, style: BobStyle, size: BobSize) => void
  onClose: () => void
}

export const BobPickerModal: React.FC<BobPickerModalProps> = ({ onInsert, onClose }) => {
  const [prompt, setPrompt] = useState('')
  const [style, setStyle] = useState<BobStyle>('mono_chrome')
  const [size, setSize] = useState<BobSize>('16x16')
  const [previewKey, setPreviewKey] = useState(0)

  const handleInsert = () => {
    if (!prompt.trim()) return
    onInsert(prompt, style, size)
    setPrompt('')
    setPreviewKey(k => k + 1)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 420 }}>
        <div className="modal-header">
          <h3>Insert Inline Bob</h3>
          <button className="btn-icon btn-sm" onClick={onClose}>
            <Icon name="close" size={16} />
          </button>
        </div>
        <div className="modal-body" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="modal-field">
            <label>Prompt / Description</label>
            <input type="text" className="modal-input" value={prompt}
                   onChange={e => setPrompt(e.target.value)}
                   onKeyDown={e => { if (e.key === 'Enter') handleInsert() }}
                   placeholder="e.g. heart icon, rocket, settings gear..." autoFocus />
          </div>
          <div className="modal-field">
            <label>Style</label>
            <select className="modal-select" value={style}
                    onChange={e => setStyle(e.target.value as BobStyle)}>
              <option value="mono_chrome">Mono Chrome</option>
              <option value="teletext">Teletext</option>
              <option value="full_color">Full Color</option>
            </select>
          </div>
          <div className="modal-field">
            <label>Size</label>
            <select className="modal-select" value={size}
                    onChange={e => setSize(e.target.value as BobSize)}>
              <option value="16x16">16×16</option>
              <option value="32x32">32×32</option>
            </select>
          </div>
          {prompt.trim() && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: 8, background: 'var(--m3-surface-container)', borderRadius: 6 }}>
              <span style={{ color: 'var(--m3-on-surface-variant)', fontSize: 12 }}>Preview:</span>
              <InlineBob key={previewKey} prompt={prompt} style={style} size={size} />
              <span style={{ color: 'var(--m3-on-surface-variant)', fontSize: 11, marginLeft: 'auto' }}>
                :bob:{prompt.replace(/\s+/g, '-').toLowerCase()}:
              </span>
            </div>
          )}
        </div>
        <div className="modal-footer">
          <button className="btn-secondary" onClick={onClose}>Cancel</button>
          <button className="btn-primary" onClick={handleInsert} disabled={!prompt.trim()}>Insert</button>
        </div>
      </div>
    </div>
  )
}

// ─── Bob autocomplete suggestions ───────────────────────────────
const BOB_AUTOCOMPLETE_SUGGESTIONS = [
  'heart', 'star', 'rocket', 'settings', 'gear', 'user', 'home',
  'search', 'mail', 'bell', 'clock', 'calendar', 'bookmark', 'flag',
  'lightbulb', 'idea', 'check', 'cross', 'plus', 'minus', 'arrow-up',
  'arrow-down', 'arrow-left', 'arrow-right', 'lock', 'unlock', 'cloud',
  'download', 'upload', 'trash', 'edit', 'pencil', 'eye', 'eye-off',
  'music', 'play', 'pause', 'stop', 'refresh', 'sync', 'share',
  'link', 'paperclip', 'camera', 'image', 'file', 'folder', 'tag',
]

// ─── EditorView Props ───────────────────────────────────────────
interface EditorViewProps {
  /** The current editor content */
  content: string
  /** Called when content changes */
  onChange: (content: string) => void
  /** Called when publish is requested */
  onPublish?: (content: string) => void
  /** Optional publish status message */
  publishStatus?: string | null
}

const EditorView: React.FC<EditorViewProps> = ({ content, onChange, onPublish, publishStatus }) => {
  const [showPreview, setShowPreview] = useState(false)
  const [showBobPicker, setShowBobPicker] = useState(false)
  const [bobStyle, setBobStyle] = useState<BobStyle>(() => {
    try { return (localStorage.getItem('editor-bob-style') as BobStyle) || 'mono_chrome' }
    catch { return 'mono_chrome' }
  })
  const [bobSize, setBobSize] = useState<BobSize>(() => {
    try { return (localStorage.getItem('editor-bob-size') as BobSize) || '16x16' }
    catch { return '16x16' }
  })

  // Bob autocomplete state
  const [showBobAutocomplete, setShowBobAutocomplete] = useState(false)
  const [bobAutocompleteQuery, setBobAutocompleteQuery] = useState('')
  const [bobAutocompleteIndex, setBobAutocompleteIndex] = useState(0)
  const bobAutocompleteRef = useRef<HTMLDivElement>(null)
  const editorRef = useRef<HTMLTextAreaElement>(null)

  // Persist bob picker preferences
  useEffect(() => {
    try { localStorage.setItem('editor-bob-style', bobStyle) } catch {}
  }, [bobStyle])
  useEffect(() => {
    try { localStorage.setItem('editor-bob-size', bobSize) } catch {}
  }, [bobSize])

  // Insert bob shortcode into editor
  const insertBob = useCallback((prompt: string, style: BobStyle, size: BobSize) => {
    const shortcode = `:bob:${prompt.replace(/\s+/g, '-').toLowerCase()}:`
    const ta = editorRef.current
    if (ta) {
      const start = ta.selectionStart
      const end = ta.selectionEnd
      const before = content.substring(0, start)
      const after = content.substring(end)
      const newContent = before + shortcode + after
      onChange(newContent)
      requestAnimationFrame(() => {
        ta.focus()
        const pos = start + shortcode.length
        ta.setSelectionRange(pos, pos)
      })
    } else {
      onChange(content + shortcode)
    }
    setShowBobPicker(false)
    setBobStyle(style)
    setBobSize(size)
  }, [content, onChange])

  // Filter suggestions based on query
  const filteredBobSuggestions = useMemo(() => {
    if (!bobAutocompleteQuery) return BOB_AUTOCOMPLETE_SUGGESTIONS
    const q = bobAutocompleteQuery.toLowerCase()
    return BOB_AUTOCOMPLETE_SUGGESTIONS.filter(s => s.includes(q))
  }, [bobAutocompleteQuery])

  // Insert bob from autocomplete
  const insertBobAutocomplete = useCallback((name: string) => {
    const shortcode = `:bob:${name}:`
    const ta = editorRef.current
    if (ta) {
      const start = ta.selectionStart
      const end = ta.selectionEnd
      const before = content.substring(0, start - bobAutocompleteQuery.length - 1)
      const after = content.substring(end)
      const newContent = before + shortcode + after
      onChange(newContent)
      requestAnimationFrame(() => {
        ta.focus()
        const pos = before.length + shortcode.length
        ta.setSelectionRange(pos, pos)
      })
    }
    setShowBobAutocomplete(false)
    setBobAutocompleteQuery('')
  }, [content, onChange, bobAutocompleteQuery])

  // Keyboard shortcut: Ctrl+Shift+B to open bob picker
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'b') {
        e.preventDefault()
        setShowBobPicker(v => !v)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  // Bob autocomplete: detect ":bob:" prefix in editor
  useEffect(() => {
    const ta = editorRef.current
    if (!ta) {
      setShowBobAutocomplete(false)
      return
    }
    const handleInput = () => {
      const cursorPos = ta.selectionStart
      const textBefore = content.substring(0, cursorPos)
      const match = textBefore.match(/:bob:([a-z0-9_-]*)$/i)
      if (match) {
        setBobAutocompleteQuery(match[1] || '')
        setBobAutocompleteIndex(0)
        setShowBobAutocomplete(true)
      } else {
        setShowBobAutocomplete(false)
        setBobAutocompleteQuery('')
      }
    }
    ta.addEventListener('input', handleInput)
    return () => ta.removeEventListener('input', handleInput)
  }, [content])

  // Close autocomplete on outside click
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (bobAutocompleteRef.current && !bobAutocompleteRef.current.contains(e.target as Node)) {
        setShowBobAutocomplete(false)
      }
    }
    if (showBobAutocomplete) {
      document.addEventListener('mousedown', handleClick)
    }
    return () => document.removeEventListener('mousedown', handleClick)
  }, [showBobAutocomplete])

  return (
    <div className="editor-view">
      {publishStatus && (
        <div className="editor-publish-status">{publishStatus}</div>
      )}
      <div className="editor-toolbar" style={{ display: 'flex', gap: 4, padding: '4px 8px', borderBottom: '1px solid var(--m3-outline)', alignItems: 'center' }}>
        <button className="btn-icon btn-sm" onClick={() => setShowPreview(v => !v)} title={showPreview ? 'Hide preview' : 'Show preview'}>
          <Icon name={showPreview ? 'visibility_off' : 'visibility'} size={16} />
        </button>
        {onPublish && (
          <button className="btn-icon btn-sm" onClick={() => onPublish(content)} title="Publish document">
            <Icon name="publish" size={16} />
          </button>
        )}
        <span style={{ flex: 1 }} />
        <button className="btn-icon btn-sm" onClick={() => setShowBobPicker(v => !v)} title="Insert inline bob (uVector icon)">
          <Icon name="emoji_objects" size={16} />
        </button>
        <span style={{ color: 'var(--m3-on-surface-variant)', fontSize: 11, marginRight: 4 }}>Bob</span>
      </div>
      <div className={`editor-body ${showPreview ? 'split' : ''}`} style={{ position: 'relative' }}>
        <textarea ref={editorRef} className="editor-textarea" value={content}
                  onChange={e => onChange(e.target.value)}
                  onKeyDown={e => {
                    if (showBobAutocomplete) {
                      if (e.key === 'ArrowDown') {
                        e.preventDefault()
                        setBobAutocompleteIndex(prev => Math.min(prev + 1, filteredBobSuggestions.length - 1))
                      } else if (e.key === 'ArrowUp') {
                        e.preventDefault()
                        setBobAutocompleteIndex(prev => Math.max(prev - 1, 0))
                      } else if (e.key === 'Enter' || e.key === 'Tab') {
                        if (filteredBobSuggestions.length > 0) {
                          e.preventDefault()
                          insertBobAutocomplete(filteredBobSuggestions[bobAutocompleteIndex])
                        }
                      } else if (e.key === 'Escape') {
                        setShowBobAutocomplete(false)
                      }
                    }
                  }}
                  placeholder="Start writing in Markdown..." spellCheck={false} />
        {showBobAutocomplete && filteredBobSuggestions.length > 0 && (
          <div ref={bobAutocompleteRef}
               style={{
                 position: 'absolute',
                 bottom: '100%',
                 left: 0,
                 right: 0,
                 zIndex: 100,
                 background: 'var(--m3-surface)',
                 border: '1px solid var(--m3-outline)',
                 borderRadius: '8px 8px 0 0',
                 maxHeight: 200,
                 overflow: 'auto',
                 boxShadow: '0 -4px 12px rgba(0,0,0,0.15)',
               }}>
            {filteredBobSuggestions.map((name, i) => (
              <div key={name}
                   onClick={() => insertBobAutocomplete(name)}
                   onMouseEnter={() => setBobAutocompleteIndex(i)}
                   style={{
                     padding: '6px 12px',
                     cursor: 'pointer',
                     display: 'flex',
                     alignItems: 'center',
                     gap: 8,
                     background: i === bobAutocompleteIndex ? 'var(--m3-surface-container-high)' : 'transparent',
                     color: 'var(--m3-on-surface)',
                     fontSize: 13,
                   }}>
                <InlineBob prompt={name} style="mono_chrome" size="16x16" />
                <span>:bob:<strong>{name}</strong>:</span>
              </div>
            ))}
          </div>
        )}
        {showPreview && <MarkdownPreview content={content} />}
      </div>

      {/* Bob Picker Modal */}
      {showBobPicker && (
        <BobPickerModal onInsert={insertBob} onClose={() => setShowBobPicker(false)} />
      )}
    </div>
  )
}

export default EditorView
