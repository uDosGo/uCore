/**
 * @module composables/useMarkdown
 * @description Lightweight markdown-to-HTML renderer for chat messages.
 * Ported from the renderMarkdown() function in AssistUISurface.tsx.
 * Supports: headings, bold, italic, code, links, lists, tables, blockquotes, hr.
 *
 * Slide Separator Convention:
 * - `---` on its own line = slide separator (stripped in prose mode)
 * - `---` is invisible in scroll view (removed from output)
 * - Frontmatter (YAML between `---` delimiters at start) provides metadata
 */
import { computed, type Ref } from 'vue'


function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function processInline(text: string): string {
  let result = escapeHtml(text)
  // Bold
  result = result.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // Italic
  result = result.replace(/\*(.+?)\*/g, '<em>$1</em>')
  // Strikethrough
  result = result.replace(/~~(.+?)~~/g, '<del>$1</del>')
  // Inline code
  result = result.replace(/`(.+?)`/g, '<code>$1</code>')
  // Links
  result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
  return result
}

function renderTable(rows: string[]): string {
  const parsed = rows
    .map(row => row.split('|').filter(cell => cell.trim()).map(cell => cell.trim()))
    .filter(row => !row[0]?.match(/^[-:]+$/))

  if (parsed.length === 0) return ''

  const [header, ...body] = parsed
  const headerHtml = header.map(c => `<th>${processInline(c)}</th>`).join('')
  const bodyHtml = body
    .map(row => `<tr>${row.map(c => `<td>${processInline(c)}</td>`).join('')}</tr>`)
    .join('')

  return `<table><thead><tr>${headerHtml}</tr></thead><tbody>${bodyHtml}</tbody></table>`
}

export function renderMarkdown(text: string): string {
  if (!text) return ''

  const lines = text.split('\n')
  const htmlParts: string[] = []
  let inCodeBlock = false
  let codeBuffer: string[] = []
  let codeLang = ''
  let inTable = false
  let tableBuffer: string[] = []

  const flushTable = () => {
    if (tableBuffer.length > 0) {
      htmlParts.push(renderTable(tableBuffer))
      tableBuffer = []
    }
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // Code blocks
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        htmlParts.push(`<pre><code${codeLang ? ` class="lang-${codeLang}"` : ''}>${codeBuffer.join('\n')}</code></pre>`)
        codeBuffer = []
        inCodeBlock = false
      } else {
        flushTable()
        inCodeBlock = true
        codeLang = line.slice(3).trim()
      }
      continue
    }
    if (inCodeBlock) {
      codeBuffer.push(escapeHtml(line))
      continue
    }

    // Tables
    if (line.startsWith('|') && line.endsWith('|')) {
      tableBuffer.push(line)
      inTable = true
      continue
    }
    if (inTable && !line.startsWith('|')) {
      inTable = false
      flushTable()
    }

    // Horizontal rule — only render if NOT a slide separator (---)
    // In prose mode, --- is stripped (invisible marker for slides/story breaks)
    if (/^[-]{3,}$/.test(line.trim())) {
      // Skip --- in prose mode (it's a slide separator)
      continue
    }
    // Other horizontal rules (***, ___) still render
    if (/^[*_]{3,}$/.test(line.trim())) {
      htmlParts.push('<hr />')
      continue
    }


    // Headings
    const headingMatch = line.match(/^(#{1,4})\s+(.+)/)
    if (headingMatch) {
      const level = headingMatch[1].length
      htmlParts.push(`<h${level}>${processInline(headingMatch[2])}</h${level}>`)
      continue
    }

    // Blockquote
    if (line.startsWith('> ')) {
      htmlParts.push(`<blockquote>${processInline(line.slice(2))}</blockquote>`)
      continue
    }

    // Unordered list
    const ulMatch = line.match(/^[-*+]\s+(.+)/)
    if (ulMatch) {
      htmlParts.push(`<ul><li>${processInline(ulMatch[1])}</li></ul>`)
      continue
    }

    // Ordered list
    const olMatch = line.match(/^\d+[.)]\s+(.+)/)
    if (olMatch) {
      htmlParts.push(`<ol><li>${processInline(olMatch[1])}</li></ol>`)
      continue
    }

    // Empty line
    if (line.trim() === '') continue

    // Paragraph
    htmlParts.push(`<p>${processInline(line)}</p>`)
  }

  // Flush remaining
  if (inCodeBlock) {
    htmlParts.push(`<pre><code>${codeBuffer.join('\n')}</code></pre>`)
  }
  flushTable()

  return htmlParts.join('\n')
}

/**
 * Render markdown as Marp-style slides.
 * Splits on --- slide separators and wraps each slide in a <section>.
 * Frontmatter (YAML between --- at start) is parsed and returned separately.
 */
export function renderSlides(text: string): {
  slides: string[]
  frontmatter: Record<string, string>
} {
  if (!text) return { slides: [], frontmatter: {} }

  const lines = text.split('\n')
  const slides: string[] = []
  let frontmatter: Record<string, string> = {}
  let currentSlide: string[] = []
  let inCodeBlock = false
  let inFrontmatter = false
  let frontmatterLines: string[] = []
  let lineIndex = 0

  // Parse frontmatter (YAML between --- at start)
  if (lines[0]?.trim() === '---') {
    inFrontmatter = true
    lineIndex = 1
    for (let i = 1; i < lines.length; i++) {
      if (lines[i].trim() === '---') {
        inFrontmatter = false
        lineIndex = i + 1
        break
      }
      frontmatterLines.push(lines[i])
    }
    // Simple frontmatter parsing
    for (const fl of frontmatterLines) {
      const match = fl.match(/^(\w+):\s*(.+)/)
      if (match) {
        frontmatter[match[1]] = match[2].trim()
      }
    }
  }

  // Split remaining content into slides on ---
  for (let i = lineIndex; i < lines.length; i++) {
    const line = lines[i]

    // Track code blocks to avoid splitting inside them
    if (line.startsWith('```')) {
      inCodeBlock = !inCodeBlock
      currentSlide.push(line)
      continue
    }

    // Slide separator (--- on its own line, outside code blocks)
    if (!inCodeBlock && /^---\s*$/.test(line)) {
      if (currentSlide.length > 0) {
        slides.push(currentSlide.join('\n'))
        currentSlide = []
      }
      continue
    }

    currentSlide.push(line)
  }

  // Push the last slide
  if (currentSlide.length > 0) {
    slides.push(currentSlide.join('\n'))
  }

  return { slides, frontmatter }
}

/**
 * Render slides as HTML (each slide wrapped in <section class="slide">).
 */
export function renderSlidesHTML(text: string): string {
  const { slides } = renderSlides(text)
  return slides
    .map(slide => `<section class="slide">${renderMarkdown(slide)}</section>`)
    .join('\n')
}

/**
 * @description Vue composable that returns a reactive computed HTML for a markdown ref.
 * @usage
 *   const html = useMarkdown(() => message.content)
 *   <div v-html="html" />
 */
export function useMarkdown(source: Ref<string> | (() => string)) {
  return computed(() => {
    const text = typeof source === 'function' ? source() : source.value
    return renderMarkdown(text)
  })
}

