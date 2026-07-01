/* ═══════════════════════════════════════════════════════════════════
   ProseView — Read-only document renderer with Markdown support
   ═══════════════════════════════════════════════════════════════════ */
import React from 'react'
import { renderMarkdown } from '../utils/renderMarkdown'

interface ProseDoc {
  title: string
  author?: string
  date?: string
  status?: string
  body: string
}

const DEFAULT_DOC: ProseDoc = {
  title: 'proseui — UDOUI Document Surface',
  author: 'uDos System',
  date: '2026-05-21',
  status: 'Draft',
  body: `<p>Welcome to <strong>proseui</strong>, the UDOUI document-oriented surface for uCode2.</p>
<h2>Getting Started</h2>
<p>Use the nav rail to switch between views:</p>
<ul>
  <li><strong>Board</strong> — Kanban-style workflow for tracking document progress</li>
  <li><strong>List</strong> — Table view of all documents with status and metadata</li>
  <li><strong>Prose</strong> — Read and preview rendered content</li>
  <li><strong>Editor</strong> — Write and edit Markdown documents</li>
</ul>
<h2>Colour Schemes</h2>
<p>Click the palette button in the topbar to choose from M3 colour schemes: Paper, Parchment, Modern, Forest, Sunset.</p>
<h2>Font Controls</h2>
<p>Use the A- / A+ buttons to adjust font size, and the format_size button to cycle between sans-serif, serif, and monospace.</p>
`,
}

interface ProseViewProps {
  doc?: ProseDoc
}

const ProseView: React.FC<ProseViewProps> = ({ doc = DEFAULT_DOC }) => (
  <div className="prose-view">
    <h1>{doc.title}</h1>
    <div className="prose-meta">
      {doc.author && <span>{doc.author}</span>}
      {doc.date && <span>{doc.date}</span>}
      {doc.status && <span>{doc.status}</span>}
    </div>
    <div className="prose" dangerouslySetInnerHTML={{ __html: doc.body }} />
  </div>
)

export default ProseView
