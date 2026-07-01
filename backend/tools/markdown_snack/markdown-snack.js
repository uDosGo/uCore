#!/usr/bin/env node

const { execSync } = require('child_process');
const MarkdownIt = require('markdown-it');

const md = new MarkdownIt({ html: true, linkify: true, breaks: true });

function readClipboard() {
  try {
    return execSync('pbpaste', { encoding: 'utf8' });
  } catch {
    return '';
  }
}

function writeClipboard(value) {
  try {
    execSync('pbcopy', { input: value });
  } catch {
    // Best effort.
  }
}

function validateMarkdown(input) {
  try {
    const tokens = md.parse(input, {});
    return { valid: Array.isArray(tokens), tokens: tokens.length };
  } catch (error) {
    return { valid: false, error: String(error) };
  }
}

function formatToMarkdown(input) {
  const lines = input
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => `- ${line}`);

  return lines.length ? lines.join('\n') : input;
}

function main() {
  const action = process.argv[2] || 'to-html';
  const argInput = process.argv.slice(3).join(' ');
  const input = argInput || readClipboard();

  if (action === 'to-html') {
    const html = md.render(input || '');
    console.log(html);
    writeClipboard(html);
    return;
  }

  if (action === 'validate') {
    const result = validateMarkdown(input || '');
    console.log(JSON.stringify(result));
    return;
  }

  if (action === 'format') {
    const formatted = formatToMarkdown(input || '');
    console.log(formatted);
    writeClipboard(formatted);
    return;
  }

  console.error(`Unknown action: ${action}`);
  process.exit(2);
}

main();
