/* ═══════════════════════════════════════════════════════════════════
   getFileIcon — Shared utility for mapping file types to icon names
   ═══════════════════════════════════════════════════════════════════ */

export function getFileIcon(type: string): string {
  const typeMap: Record<string, string> = {
    markdown: 'description',
    md: 'description',
    txt: 'description',
    image: 'image',
    png: 'image',
    jpg: 'image',
    jpeg: 'image',
    gif: 'image',
    svg: 'image',
    code: 'code',
    js: 'code',
    ts: 'code',
    py: 'code',
    yaml: 'code',
    json: 'data_object',
    python: 'code',
    typescript: 'code',
  }
  return typeMap[type?.toLowerCase()] || 'insert_drive_file'
}
