---
description: Always enforce Right-to-Left (RTL) formatting and HTML wrapper for all Hebrew text, responses, code blocks, lists, and tables across all conversations and projects.
globs: "*"
---

# Hebrew RTL Mandatory Wrapper Rule

## Primary Mandate
Every single response containing Hebrew text MUST be completely wrapped in a Right-to-Left HTML block:

<div dir="rtl" style="text-align: right;">
(Content goes here)
</div>

## Execution Directives
1. ALWAYS start Hebrew responses with `<div dir="rtl" style="text-align: right;">`.
2. ALWAYS end Hebrew responses with `</div>`.
3. Ensure all bullet lists, numbered lists, markdown tables, and headers flow naturally from right to left inside the wrapper.
4. When mixing Hebrew with technical English terms (e.g. Python, GitHub, API, MCP), keep the layout strictly RTL without LTR text distortion.
