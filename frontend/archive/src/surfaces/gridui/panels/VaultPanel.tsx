/* ═══════════════════════════════════════════════════════════════════
   VaultPanel — Ceetex document viewer
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState } from 'react'
import { useStore } from '../GridUIStore'

const MOCK_DOCS = [
  { id: 'doc-1', title: 'USX Grid Specification', type: 'spec', content: '# USX Grid Specification\n\nThe USX grid format defines a character-based display system...', tags: ['spec', 'grid', 'usx'] },
  { id: 'doc-2', title: 'C64 Memory Map', type: 'reference', content: '# C64 Memory Map\n\n$0000-$00FF: Zero Page\n$0100-$01FF: Stack...', tags: ['c64', 'memory', 'reference'] },
  { id: 'doc-3', title: 'Teletext Standards', type: 'spec', content: '# Teletext Standards\n\nWorld System Teletext (WST) defines...', tags: ['teletext', 'standard', 'broadcast'] },
  { id: 'doc-4', title: 'Font Encoding Guide', type: 'guide', content: '# Font Encoding Guide\n\nCharacter encoding for 128-character sets...', tags: ['font', 'encoding', 'guide'] },
  { id: 'doc-5', title: 'GridUI Architecture', type: 'doc', content: '# GridUI Architecture\n\nThe GridUI surface provides a retro computing interface...', tags: ['architecture', 'gridui', 'react'] },
]

export function VaultPanel() {
  const store = useStore()
  const [docs] = useState(MOCK_DOCS)
  const [selectedDoc, setSelectedDoc] = useState<typeof MOCK_DOCS[0] | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeTag, setActiveTag] = useState<string | null>(null)

  const allTags = Array.from(new Set(docs.flatMap(d => d.tags)))
  const filteredDocs = docs.filter(d => {
    if (activeTag && !d.tags.includes(activeTag)) return false
    if (searchQuery && !d.title.toLowerCase().includes(searchQuery.toLowerCase()) && !d.content.toLowerCase().includes(searchQuery.toLowerCase())) return false
    return true
  })

  return (
    <div className="gridui-panel">
      <div className="gridui-filter-bar">
        <input value={searchQuery} onChange={e => setSearchQuery(e.target.value)} placeholder="Search documents..." className="gridui-input" style={{ width: 180 }} />

        <button onClick={() => setActiveTag(null)} className={`gridui-filter-btn ${!activeTag ? 'gridui-filter-btn--active' : 'gridui-filter-btn--inactive'}`}>All</button>
        {allTags.map(tag => (
          <button key={tag} onClick={() => setActiveTag(tag === activeTag ? null : tag)} className={`gridui-filter-btn ${activeTag === tag ? 'gridui-filter-btn--active' : 'gridui-filter-btn--inactive'}`}>{tag}</button>
        ))}
      </div>
      <div className="gridui-vault-layout">
        <div className="gridui-vault-sidebar">
          {filteredDocs.map(doc => (
            <div key={doc.id} onClick={() => setSelectedDoc(doc)} className={`gridui-vault-doc ${selectedDoc?.id === doc.id ? 'gridui-vault-doc--active' : ''}`}>
              <div className="gridui-vault-doc-title">{doc.title}</div>
              <div className="gridui-vault-doc-type">{doc.type}</div>
            </div>
          ))}
          {filteredDocs.length === 0 && <div className="gridui-empty" style={{ padding: 16 }}>No documents found</div>}
        </div>
        <div className="gridui-vault-content">
          {selectedDoc ? (
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, color: 'var(--grid-text, #e6edf3)' }}>{selectedDoc.title}</h3>
                <span className="gridui-tag" style={{ background: 'rgba(88,166,255,0.15)', color: '#58a6ff', textTransform: 'none' }}>{selectedDoc.type}</span>
              </div>
              <div style={{ display: 'flex', gap: 4, marginBottom: 12 }}>
                {selectedDoc.tags.map(tag => <span key={tag} className="gridui-tag" style={{ background: 'var(--grid-border-light, #21262d)', color: 'var(--grid-text-secondary, #8b949e)', textTransform: 'none' }}>#{tag}</span>)}
              </div>
              <pre className="gridui-vault-pre">{selectedDoc.content}</pre>
            </div>
          ) : (
            <div className="gridui-empty">
              <span style={{ fontSize: 32 }}>📄</span>
              <span style={{ fontSize: 14 }}>Select a document to view</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
