/* ═══════════════════════════════════════════════════════════════════
   KanbanBoard — Shared Kanban board component
   Extracted from ProseUISurfaceView and MissionControlSurface
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState } from 'react'
import { Icon } from './Icon'

export interface KanbanItem {
  id: string
  title: string
  type: string
  date: string
}

export interface KanbanColumn {
  id: string
  title: string
  color: string
  items: KanbanItem[]
}

interface KanbanBoardProps {
  columns: KanbanColumn[]
  onItemClick?: (item: KanbanItem, column: KanbanColumn) => void
  onItemDelete?: (itemId: string) => void
  onItemMove?: (item: KanbanItem, fromColId: string, toColId: string) => void
  onAddCard?: (colId: string, title: string) => void
  readOnly?: boolean
}

const KanbanBoard: React.FC<KanbanBoardProps> = ({
  columns: initialColumns,
  onItemClick,
  onItemDelete,
  onItemMove,
  onAddCard,
  readOnly = false,
}) => {
  const [columns, setColumns] = useState<KanbanColumn[]>(initialColumns)
  const [dragItem, setDragItem] = useState<{ item: KanbanItem; colId: string } | null>(null)
  const [showAddCard, setShowAddCard] = useState(false)
  const [addCardCol, setAddCardCol] = useState('')
  const [addCardTitle, setAddCardTitle] = useState('')

  const handleDragStart = (item: KanbanItem, colId: string) => {
    setDragItem({ item, colId })
  }

  const handleDrop = (targetColId: string) => {
    if (!dragItem || dragItem.colId === targetColId) {
      setDragItem(null)
      return
    }
    if (onItemMove) {
      onItemMove(dragItem.item, dragItem.colId, targetColId)
    }
    setColumns(prev => {
      const next = prev.map(col => ({ ...col, items: [...col.items] }))
      const srcCol = next.find(c => c.id === dragItem.colId)
      const tgtCol = next.find(c => c.id === targetColId)
      if (!srcCol || !tgtCol) return prev
      const idx = srcCol.items.findIndex(i => i.id === dragItem.item.id)
      if (idx === -1) return prev
      const [moved] = srcCol.items.splice(idx, 1)
      tgtCol.items.push(moved)
      return next
    })
    setDragItem(null)
  }

  const handleDelete = (itemId: string) => {
    setColumns(prev => prev.map(col => ({
      ...col,
      items: col.items.filter(i => i.id !== itemId),
    })))
    onItemDelete?.(itemId)
  }

  const openAddCard = (colId: string) => {
    setAddCardCol(colId)
    setAddCardTitle('')
    setShowAddCard(true)
  }

  const confirmAddCard = () => {
    if (!addCardTitle.trim()) return
    const newItem: KanbanItem = {
      id: `card-${Date.now()}`,
      title: addCardTitle.trim(),
      type: 'doc',
      date: 'just now',
    }
    setColumns(prev => prev.map(col =>
      col.id === addCardCol ? { ...col, items: [...col.items, newItem] } : col
    ))
    onAddCard?.(addCardCol, addCardTitle.trim())
    setShowAddCard(false)
    setAddCardTitle('')
  }

  return (
    <div className="kanban-board">
      {columns.map(col => (
        <div key={col.id} className="kanban-col"
             onDragOver={e => e.preventDefault()}
             onDrop={() => handleDrop(col.id)}>
          <div className="kanban-col-header">
            <span className="kanban-col-dot" style={{ background: col.color }} />
            <span className="kanban-col-title">{col.title}</span>
            <span className="kanban-col-count">{col.items.length}</span>
            {!readOnly && (
              <button className="kanban-add-btn" onClick={() => openAddCard(col.id)} title="Add card">
                <Icon name="add" size={14} />
              </button>
            )}
          </div>
          <div className="kanban-col-body">
            {col.items.map(item => (
              <div key={item.id} className="kanban-card"
                   draggable={!readOnly}
                   onDragStart={() => !readOnly && handleDragStart(item, col.id)}
                   onClick={() => onItemClick?.(item, col)}>
                <div className="kanban-card-header">
                  <div className="kanban-card-title">{item.title}</div>
                  {!readOnly && (
                    <button className="kanban-card-delete" onClick={(e) => { e.stopPropagation(); handleDelete(item.id) }} title="Delete card">
                      <Icon name="close" size={12} />
                    </button>
                  )}
                </div>
                <div className="kanban-card-meta">
                  <span className="kanban-card-type">{item.type}</span>
                  <span className="kanban-card-date">{item.date}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {/* Add Card Dialog */}
      {showAddCard && (
        <div className="modal-overlay" onClick={() => setShowAddCard(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 400 }}>
            <div className="modal-header">
              <h3>Add Card</h3>
              <button className="btn-icon btn-sm" onClick={() => setShowAddCard(false)}>
                <Icon name="close" size={16} />
              </button>
            </div>
            <div className="modal-body">
              <input type="text" className="modal-input" value={addCardTitle}
                     onChange={e => setAddCardTitle(e.target.value)}
                     onKeyDown={e => { if (e.key === 'Enter') confirmAddCard() }}
                     placeholder="Card title..." autoFocus />
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowAddCard(false)}>Cancel</button>
              <button className="btn-primary" onClick={confirmAddCard} disabled={!addCardTitle.trim()}>Add</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default KanbanBoard
