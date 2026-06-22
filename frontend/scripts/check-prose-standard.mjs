import fs from 'node:fs'
import path from 'node:path'

const ROOT = path.resolve(process.cwd(), 'src')
const TARGET_EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.css'])
const FORBIDDEN_TOKEN = 'prose-body'

function walk(dir, files = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true })
  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      walk(fullPath, files)
      continue
    }
    if (TARGET_EXTENSIONS.has(path.extname(entry.name))) {
      files.push(fullPath)
    }
  }
  return files
}

function findForbiddenUsages(filePath) {
  const content = fs.readFileSync(filePath, 'utf8')
  const lines = content.split(/\r?\n/)
  const hits = []
  for (let i = 0; i < lines.length; i += 1) {
    if (lines[i].includes(FORBIDDEN_TOKEN)) {
      hits.push({
        file: path.relative(process.cwd(), filePath),
        line: i + 1,
        text: lines[i].trim(),
      })
    }
  }
  return hits
}

if (!fs.existsSync(ROOT)) {
  console.error('Missing frontend source directory:', ROOT)
  process.exit(1)
}

const files = walk(ROOT)
const violations = files.flatMap(findForbiddenUsages)

if (violations.length > 0) {
  console.error('Deprecated prose class detected. Use .prose instead of prose-body.')
  for (const v of violations) {
    console.error(`- ${v.file}:${v.line} ${v.text}`)
  }
  process.exit(1)
}

console.log('Prose class guard passed: no prose-body usage found in frontend/src.')