/* ═══════════════════════════════════════════════════════════════════
   ProseDiffEditor — CodeMirror 6 merge-based diff editor with
   approve/reject/modify controls for ProseUI MCP approval workflow.
   Uses USX design tokens via CSS custom properties.
   ═══════════════════════════════════════════════════════════════════ */
import React, { useEffect, useRef, useState, useCallback } from 'react'
import { MergeView } from '@codemirror/merge'
import { EditorView, basicSetup } from 'codemirror'
import { python } from '@codemirror/lang-python'
import { yaml } from '@codemirror/lang-yaml'
import { markdown } from '@codemirror/lang-markdown'
import { javascript } from '@codemirror/lang-javascript'
import { html } from '@codemirror/lang-html'
import { css } from '@codemirror/lang-css'
import { StreamLanguage } from '@codemirror/language'
import { simpleMode } from '@codemirror/legacy-modes/mode/simple-mode'
import { Icon } from './Icon'

/* ─── Types ─────────────────────────────────────────────────────── */

export interface DiffChange {
  from: number
  to: number
  original: string
  modified: string
  accepted: boolean
  rejected: boolean
}

export interface ProseDiffEditorProps {
  /** The original (before) content */
  original: string
  /** The modified (after) content */
  modified: string
  /** Language for syntax highlighting */
  language?: 'python' | 'yaml' | 'markdown' | 'javascript' | 'typescript' | 'html' | 'css' | 'basic' | 'teletext'
  /** Optional filename for display */
  filename?: string
  /** Called when user approves a specific change */
  onApproveChange?: (change: DiffChange) => void
  /** Called when user rejects a specific change */
  onRejectChange?: (change: DiffChange) => void
  /** Called when user approves all changes */
  onApproveAll?: () => void
  /** Called when user rejects all changes */
  onRejectAll?: () => void
  /** Called when user wants to open in USXD for deeper editing */
  onModifyInUSXD?: () => void
  /** Whether the editor is read-only */
  readOnly?: boolean
}

/* ─── Language Extensions ────────────────────────────────────────── */

const languageExtensions: Record<string, any> = {
  python: python(),
  yaml: yaml(),
  markdown: markdown(),
  javascript: javascript(),
  typescript: javascript({ typescript: true }),
  html: html(),
  css: css(),
  basic: StreamLanguage.define(simpleMode({
    start: [
      { regex: /REM.*$/, token: 'comment' },
      { regex: /PRINT|INPUT|LET|IF|THEN|ELSE|FOR|NEXT|WHILE|WEND|GOTO|GOSUB|RETURN|END|STOP|READ|DATA|DIM|CLS|RUN|LIST|NEW|LOAD|SAVE/, token: 'keyword' },
      { regex: /[0-9]+/, token: 'number' },
      { regex: /"[^"]*"/, token: 'string' },
      { regex: /[A-Za-z_][A-Za-z0-9_]*/, token: 'variable' },
    ],
  })),
  teletext: StreamLanguage.define(simpleMode({
    start: [
      { regex: /\^[A-Z]/, token: 'control' },
      { regex: /[0-9A-F]{2}/, token: 'hex' },
      { regex: /[A-Za-z0-9\s]+/, token: 'text' },
    ],
  })),
}

/* ─── Component ──────────────────────────────────────────────────── */

const ProseDiffEditor: React.FC<ProseDiffEditorProps> = ({
  original,
  modified,
  language = 'markdown',
  filename,
  onApproveChange,
  onRejectChange,
  onApproveAll,
  onRejectAll,
  onModifyInUSXD,
  readOnly = false,
}) => {
  const containerRef = useRef<HTMLDivElement>(null)
  const mergeViewRef = useRef<MergeView | null>(null)
  const [status, setStatus] = useState<'pending' | 'approved' | 'rejected' | 'modified'>('pending')

  // Compute simple change stats
  const origLines = original.split('\n')
  const modLines = modified.split('\n')
  const addedLines = modLines.length - origLines.length
  const removedLines = origLines.length - modLines.length
  const totalChanges = Math.abs(addedLines) + Math.abs(removedLines)

  useEffect(() => {
    if (!containerRef.current) return

    // Clean up previous instance
    if (mergeViewRef.current) {
      mergeViewRef.current.destroy()
    }

    const langExt = languageExtensions[language] || basicSetup
    const extensions = [basicSetup, langExt]

    mergeViewRef.current = new MergeView({
      a: { doc: original, extensions },
      b: {
        doc: modified,
        extensions: readOnly ? [EditorView.editable.of(false)] : extensions,
      },
      parent: containerRef.current,
      revertControls: 'a-to-b',
      highlightChanges: true,
    })

    return () => {
      mergeViewRef.current?.destroy()
    }
  }, [original, modified, language, readOnly])

  const handleApproveAll = useCallback(() => {
    setStatus('approved')
    onApproveAll?.()
  }, [onApproveAll])

  const handleRejectAll = useCallback(() => {
    setStatus('rejected')
    onRejectAll?.()
  }, [onRejectAll])

  const handleModifyInUSXD = useCallback(() => {
    onModifyInUSXD?.()
  }, [onModifyInUSXD])

  return (
    <div className="prose-diff-editor" style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: 'var(--pico-card-background-color, #161b22)',
      border: '1px solid var(--pico-border-color, #30363d)',
      borderRadius: 'var(--pico-border-radius, 6px)',
      overflow: 'hidden',
      fontFamily: 'var(--pico-font-family, "SF Mono", "Fira Code", monospace)',
      fontSize: '0.8rem',
    }}>
      {/* ═══ Toolbar ═══ */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.35rem 0.75rem',
        background: 'var(--pico-background-color, #0d1117)',
        borderBottom: '1px solid var(--pico-border-color, #30363d)',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--pico-muted-color, #8b949e)' }}>
            {filename || 'untitled'}
          </span>
          <span style={{
            padding: '0.1rem 0.35rem',
            borderRadius: '3px',
            background: 'var(--pico-card-sectioning-background-color, #1c2128)',
            fontSize: '0.65rem',
            color: 'var(--pico-muted-color, #8b949e)',
          }}>
            {language}
          </span>
          {status !== 'pending' && (
            <span style={{
              padding: '0.1rem 0.35rem',
              borderRadius: '3px',
              fontSize: '0.65rem',
              background: status === 'approved' ? 'var(--pico-primary, #58a6ff)' :
                          status === 'rejected' ? 'var(--pico-del-color, #f85149)' :
                          'var(--pico-ins-color, #3fb950)',
              color: status === 'approved' ? 'var(--pico-primary, #58a6ff)' :
                     status === 'rejected' ? 'var(--pico-del-color, #f85149)' :
                     'var(--pico-ins-color, #3fb950)',
            }}>
              {status === 'approved' ? '✓ Approved' :
               status === 'rejected' ? '✗ Rejected' :
               '✎ Modified'}
            </span>
          )}
        </div>

        <div style={{ display: 'flex', gap: '0.35rem' }}>
          {onApproveAll && status === 'pending' && (
            <button
              onClick={handleApproveAll}
              style={{
                padding: '0.2rem 0.5rem',
                fontSize: '0.7rem',
                borderRadius: '4px',
                border: 'none',
                background: 'var(--pico-primary, #58a6ff)',
                color: 'var(--pico-primary, #58a6ff)',
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              ✓ Approve All
            </button>
          )}
          {onRejectAll && status === 'pending' && (
            <button
              onClick={handleRejectAll}
              style={{
                padding: '0.2rem 0.5rem',
                fontSize: '0.7rem',
                borderRadius: '4px',
                border: 'none',
                background: 'var(--pico-del-color, #f85149)',
                color: 'var(--pico-del-color, #f85149)',
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              ✗ Reject All
            </button>
          )}
          {onModifyInUSXD && (
            <button
              onClick={handleModifyInUSXD}
              style={{
                padding: '0.2rem 0.5rem',
                fontSize: '0.7rem',
                borderRadius: '4px',
                border: '1px solid var(--pico-border-color, #30363d)',
                background: 'transparent',
                color: 'var(--pico-primary, #58a6ff)',
                cursor: 'pointer',
                fontFamily: 'inherit',
              }}
            >
              Open in USXD
            </button>
          )}
        </div>
      </div>

      {/* ═══ Diff Container ═══ */}
      <div ref={containerRef} style={{ flex: 1, overflow: 'auto' }} />

      {/* ═══ Change Summary ═══ */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
        padding: '0.2rem 0.75rem',
        background: 'var(--pico-background-color, #0d1117)',
        borderTop: '1px solid var(--pico-border-color, #30363d)',
        fontSize: '0.65rem',
        color: 'var(--pico-muted-color, #8b949e)',
        flexShrink: 0,
      }}>
        <span style={{ color: 'var(--pico-primary, #58a6ff)' }}>+{Math.abs(addedLines)}</span>
        <span style={{ color: 'var(--pico-del-color, #f85149)' }}>-{Math.abs(removedLines)}</span>
        <span>~{totalChanges} changes</span>
        <span style={{ opacity: 0.5 }}>|</span>
        <span>{origLines.length} → {modLines.length} lines</span>
      </div>
    </div>
  )
}

export default ProseDiffEditor
