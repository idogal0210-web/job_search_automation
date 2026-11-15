---
trigger: always_on
description: "Enforce strict zero-emoji policy across all code, comments, documentation, commit messages, PRs, and chat responses."
---

# Zero-Emoji Mandatory Rule

## 1. Absolute Invariant
Strictly ZERO EMOJIS across all code files, comments, docstrings, documentation files (Markdown, HTML, Text), Git commit messages, Pull Request descriptions, and chat conversation responses.

## 2. Replacement Guidelines
- Never use pictorial Unicode emojis (such as rockets, checkmarks, warning triangles, folder icons, tools, sparkles).
- Never use Dingbat symbols (Unicode range `U+2700 - U+27BF`, such as `U+2715` Multiplication X) in JavaScript string comparisons, template literals, or DOM selectors for close/clear buttons. Always use standard ASCII `'x'`, CSS class names (`.search-clear-btn`, `.btn-clear-search`), or Phosphor vector icon classes (`.ph-x`).
- Use clean, professional typographic formatting instead:
  - Bullet lists (`-`, `*`)
  - Clear text labels (`[OK]`, `[FAILED]`, `[WARNING]`, `[INFO]`)
  - Bold headers and Markdown emphasis
  - Clean HTML structure (`<div>`, `<span>`, `<code>`)

## 3. Pre-Commit & Output Guard
Before finalizing any response, committing code, or writing documentation, verify that the output contains zero emoji characters.
