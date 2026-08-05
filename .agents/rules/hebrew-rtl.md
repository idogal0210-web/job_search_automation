# Hebrew RTL (Right-to-Left) Formatting Rule

## Overview
This rule enforces strict Right-to-Left (RTL) formatting and writing for all Hebrew outputs, chat communications, email templates, and web interfaces across Antigravity.

## Core Directives

### 1. Chat & Conversational Hebrew
- All Hebrew text generated in chat responses must follow proper Right-to-Left (RTL) logical structure.
- Align bullet lists, headers, and numbered lists to flow naturally from right to left.
- When mixing Hebrew with English technical terms (e.g. "Gemini API", "GitHub Actions", "Python"), format the surrounding punctuation and sentence layout so the Hebrew text reads right-to-left without layout distortion.

### 2. HTML Templates, Web Apps, and Email Reports
- Every generated HTML template, web app, or email summary MUST include:
  - `<html dir="rtl" lang="he">`
  - `<body dir="rtl">`
- Apply explicit CSS rules: `direction: rtl; text-align: right;` to all container elements, cards, tables, headers, and text blocks.
- Ensure badges, buttons, and call-to-action links align properly to the right margin.

### 3. Artifacts and Generated Documents
- Any generated Markdown, HTML, PDF, or text artifacts containing Hebrew must prioritize RTL alignment and readability.
