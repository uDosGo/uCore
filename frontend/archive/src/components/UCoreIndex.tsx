/* ═══════════════════════════════════════════════════════════════════
   UCoreIndex — Central index and search for uCore ecosystem
   ═══════════════════════════════════════════════════════════════════ */
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Icon } from './Icon'

interface UCoreIndexProps {
  open?: boolean
  onClose?: () => void
}

interface IndexItem {
  name: string
  type: string
  path: string
  description?: string
  exports?: string[]
  route?: string
  _score?: number
}

interface IndexData {
  meta: {
    version: string
    generated_at: string
    ucore_version: string
  }
  skills: IndexItem[]
  mcp_servers: IndexItem[]
  surfaces: IndexItem[]
  components: IndexItem[]
  config_files: IndexItem[]
  documentation: IndexItem[]
}

export const UCoreIndex: React.FC<UCoreIndexProps> = ({ open = true, onClose }) => {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState<string>('all')
  const [results, setResults] = useState<IndexItem[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [indexData, setIndexData] = useState<IndexData | null>(null)

  // Fetch index data on mount
  useEffect(() => {
    fetchIndex()
  }, [])

  // Search when query changes
  useEffect(() => {
    if (query.length >= 2) {
      performSearch()
    } else if (query.length === 0) {
      setResults([])
      setTotal(0)
    }
  }, [query, category])

  const fetchIndex = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8484/api/skills/ucore_index/run')
      const data = await response.json()
      if (data.index) {
        setIndexData(data.index)
      }
    } catch (error) {
      console.error('Failed to fetch index:', error)
    } finally {
      setLoading(false)
    }
  }

  const performSearch = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://localhost:8484/api/skills/ucore_index/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ search: query, category: category === 'all' ? undefined : category, limit: 50 }),
      })
      const data = await response.json()
      if (data.results) {
        setResults(data.results)
        setTotal(data.total)
      }
    } catch (error) {
      console.error('Search failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const getCategoryColor = (type: string) => {
    const colors: Record<string, string> = {
      'Skill': '#58a6ff',
      'MCP Server': '#3fb950',
      'Surface': '#d29922',
      'React Component': '#a371f7',
      'Configuration': '#f85149',
      'Documentation': '#7ee787',
    }
    return colors[type] || '#8b949e'
  }

  const getCategoryIcon = (type: string) => {
    const icons: Record<string, string> = {
      'Skill': 'terminal',
      'MCP Server': 'server',
      'Surface': 'layout',
      'React Component': 'box',
      'Configuration': 'settings',
      'Documentation': 'book',
    }
    return icons[type] || 'info'
  }

  if (!open) return null

  return (
    <div className="ucore-index-overlay" onClick={onClose}>
      <div className="ucore-index-panel" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="ucore-index-header">
          <div className="ucore-index-title">
            <Icon name="database" size={20} />
            <h1>uCore Index</h1>
          </div>
          <div className="ucore-index-actions">
            <button
              className="ucore-index-back"
              onClick={() => navigate('/')}
            >
              <Icon name="home" size={14} />
              <span>Dashboard</span>
            </button>
            <button className="ucore-index-close" onClick={onClose}>
              <Icon name="x" size={16} />
            </button>
          </div>
        </div>

        {/* Search */}
        <div className="ucore-index-search">
          <Icon name="search" size={14} />
          <input
            type="text"
            placeholder="Search skills, surfaces, components..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="ucore-index-input"
          />
          {query && (
            <button
              className="ucore-index-clear"
              onClick={() => setQuery('')}
            >
              <Icon name="x" size={12} />
            </button>
          )}
        </div>

        {/* Category Filters */}
        <div className="ucore-index-categories">
          <button
            className={`ucore-index-category ${category === 'all' ? 'ucore-index-category--active' : ''}`}
            onClick={() => setCategory('all')}
          >
            All ({total})
          </button>
          <button
            className={`ucore-index-category ${category === 'Skill' ? 'ucore-index-category--active' : ''}`}
            onClick={() => setCategory('Skill')}
          >
            Skills ({indexData?.skills.length || 0})
          </button>
          <button
            className={`ucore-index-category ${category === 'Surface' ? 'ucore-index-category--active' : ''}`}
            onClick={() => setCategory('Surface')}
          >
            Surfaces ({indexData?.surfaces.length || 0})
          </button>
          <button
            className={`ucore-index-category ${category === 'React Component' ? 'ucore-index-category--active' : ''}`}
            onClick={() => setCategory('React Component')}
          >
            Components ({indexData?.components.length || 0})
          </button>
          <button
            className={`ucore-index-category ${category === 'Documentation' ? 'ucore-index-category--active' : ''}`}
            onClick={() => setCategory('Documentation')}
          >
            Docs ({indexData?.documentation.length || 0})
          </button>
        </div>

        {/* Results */}
        <div className="ucore-index-results">
          {loading ? (
            <div className="ucore-index-loading">
              <div className="ucore-index-spinner" />
              <span>Searching...</span>
            </div>
          ) : results.length === 0 ? (
            <div className="ucore-index-empty">
              <Icon name="search" size={32} />
              <p>No results found</p>
              <p className="ucore-index-empty-hint">
                Try a different search term or category
              </p>
            </div>
          ) : (
            <div className="ucore-index-list">
              {results.map((item, idx) => (
                <div key={idx} className="ucore-index-item">
                  <div className="ucore-index-item-header">
                    <div
                      className="ucore-index-item-icon"
                      style={{ backgroundColor: `${getCategoryColor(item.type)}20` }}
                    >
                      <Icon name={getCategoryIcon(item.type)} size={14} />
                    </div>
                    <div className="ucore-index-item-info">
                      <span className="ucore-index-item-name">{item.name}</span>
                      <span className="ucore-index-item-type">{item.type}</span>
                    </div>
                    {item._score && (
                      <span className="ucore-index-item-score">
                        {item._score} pts
                      </span>
                    )}
                  </div>
                  {item.description && (
                    <p className="ucore-index-item-description">{item.description}</p>
                  )}
                  {item.path && (
                    <div className="ucore-index-item-path">
                      <Icon name="file" size={10} />
                      <span>{item.path}</span>
                    </div>
                  )}
                  {item.route && (
                    <div className="ucore-index-item-route">
                      <Icon name="link" size={10} />
                      <span>/{item.route}</span>
                    </div>
                  )}
                  {item.exports && item.exports.length > 0 && (
                    <div className="ucore-index-item-exports">
                      {item.exports.slice(0, 3).map((exp, i) => (
                        <code key={i} className="ucore-index-export">
                          {exp}
                        </code>
                      ))}
                      {item.exports.length > 3 && (
                        <span className="ucore-index-export-more">
                          +{item.exports.length - 3} more
                        </span>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="ucore-index-footer">
          <span className="ucore-index-stats">
            Showing {results.length} of {total} results
          </span>
          <button
            className="ucore-index-refresh"
            onClick={fetchIndex}
          >
            <Icon name="refresh" size={12} />
            Refresh
          </button>
        </div>
      </div>
    </div>
  )
}

export default UCoreIndex