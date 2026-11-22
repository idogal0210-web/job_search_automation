---
trigger: always_on
description: "Mandates using scripts/render_tree_widget.py to render an interactive Generative UI tree widget (<agent-embed>) whenever the user requests the project tree."
---

# נוהל הצגת עץ הפרויקט (Project Tree Display Policy)

Whenever the user asks to see or inspect the project tree, file structure, or repository hierarchy (e.g. "הצג עץ", "עץ הפרויקט", "מה מבנה הפרויקט", "הצג מבנה תיקיות", "project tree"):

1. The agent MUST NOT dump raw ASCII trees, plain Markdown text lists, or unconstrained shell listings (`tree`, `find .`, `ls -R`).
2. The agent MUST execute the dedicated project generator script:
   ```bash
   python3 scripts/render_tree_widget.py --output "<artifact_dir>/tree_widget.html"
   ```
   (if `<artifact_dir>` is not known, running `python3 scripts/render_tree_widget.py` defaults to `docs/tree_widget.html`).
3. The agent MUST embed the generated interactive widget into its response using the native tag:
   ```html
   <agent-embed src="file:///<path_to_html>"></agent-embed>
   ```
