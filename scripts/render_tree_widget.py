#!/usr/bin/env python3
"""
render_tree_widget.py
Generates an interactive, token-efficient HTML tree widget (Generative UI)
representing the updated repository directory tree with Git change annotations.
Designed for job_search_automation to run at the conclusion of tasks.
Strictly adheres to zero-emoji and resilient execution standards.
"""

import argparse
import html
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

EXCLUDED_DIR_NAMES = {
    ".git",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
}

EXCLUDED_FILE_NAMES = {
    ".DS_Store",
    ".gitignore",
}


def get_git_status(repo_dir: Path) -> Tuple[Dict[str, str], int, int, int]:
    """
    Parses git status --porcelain to map relative paths to status codes.
    Returns: (status_map, modified_count, added_count, deleted_count)
    """
    status_map: Dict[str, str] = {}
    mod_count = 0
    add_count = 0
    del_count = 0

    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if len(line) < 4:
                    continue
                code = line[:2].strip()
                rel_path = line[3:].strip()
                # Handle renamed files 'R  orig -> dest'
                if " -> " in rel_path:
                    rel_path = rel_path.split(" -> ")[1].strip()

                norm_path = str(Path(rel_path))
                if "M" in code:
                    status_map[norm_path] = "modified"
                    mod_count += 1
                elif "A" in code or "??" in code:
                    status_map[norm_path] = "new"
                    add_count += 1
                elif "D" in code:
                    status_map[norm_path] = "deleted"
                    del_count += 1
    except Exception:
        pass

    return status_map, mod_count, add_count, del_count


def build_tree_data(repo_dir: Path, max_depth: int = 3) -> Dict:
    """
    Recursively scans directory tree up to max_depth and returns a nested dict.
    """
    def scan_dir(current: Path, depth: int) -> Dict:
        name = current.name or repo_dir.name
        rel = str(current.relative_to(repo_dir)) if current != repo_dir else ""
        node = {
            "name": name,
            "path": rel,
            "is_dir": True,
            "children": [],
        }

        if depth >= max_depth:
            return node

        try:
            entries = sorted(list(current.iterdir()), key=lambda p: (not p.is_dir(), p.name.lower()))
            for entry in entries:
                if entry.is_dir():
                    if entry.name in EXCLUDED_DIR_NAMES:
                        continue
                    node["children"].append(scan_dir(entry, depth + 1))
                else:
                    if entry.name in EXCLUDED_FILE_NAMES:
                        continue
                    node["children"].append({
                        "name": entry.name,
                        "path": str(entry.relative_to(repo_dir)),
                        "is_dir": False,
                    })
        except Exception:
            pass

        return node

    return scan_dir(repo_dir, 0)


def generate_html_widget(
    tree_data: Dict,
    status_map: Dict[str, str],
    mod_count: int,
    add_count: int,
    del_count: int,
    task_title: str = "עדכון מבנה הפרויקט",
) -> str:
    """
    Renders a self-contained, responsive HTML widget with Tailwind CSS.
    """
    def render_node(node: Dict, node_id_prefix: str, idx: int) -> Tuple[str, bool]:
        node_id = f"{node_id_prefix}-{idx}"
        is_dir = node.get("is_dir", False)
        name = html.escape(node.get("name", ""))
        rel_path = node.get("path", "")
        status = status_map.get(rel_path, "")

        if not is_dir:
            badge_html = ""
            if status == "modified":
                badge_html = '<span class="badge-modified text-[10px] px-1.5 py-0.5 rounded font-sans font-medium">עודכן</span>'
            elif status == "new":
                badge_html = '<span class="badge-new text-[10px] px-1.5 py-0.5 rounded font-sans font-medium">חדש</span>'
            elif status == "deleted":
                badge_html = '<span class="badge-deleted text-[10px] px-1.5 py-0.5 rounded font-sans font-medium">הוסר</span>'

            has_change = bool(status)
            item_html = f'''
            <div class="tree-node flex items-center justify-between py-1 px-2 rounded">
              <span class="text-slate-700 dark:text-slate-300 font-mono">{name}</span>
              {badge_html}
            </div>'''
            return item_html, has_change

        # Folder handling
        children_html_list = []
        any_child_changed = False
        children = node.get("children", [])

        for c_idx, child in enumerate(children):
            c_html, c_changed = render_node(child, node_id, c_idx)
            children_html_list.append(c_html)
            if c_changed:
                any_child_changed = True

        children_block = "".join(children_html_list)
        count_label = f"{len(children)} פריטים"
        arrow = "▼" if any_child_changed else "◀"
        hidden_class = "" if any_child_changed else "hidden"

        folder_html = f'''
        <div class="folder-group">
          <div class="tree-node flex items-center justify-between py-1 px-2 rounded cursor-pointer" onclick="toggleFolder('{node_id}')">
            <div class="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-200">
              <span id="{node_id}-arrow" class="text-slate-400 font-mono text-xs">{arrow}</span>
              <span>{name}/</span>
            </div>
            <span class="text-xs text-slate-400 font-sans">{count_label}</span>
          </div>
          <div id="{node_id}" class="{hidden_class} pr-4 border-r border-slate-200 dark:border-slate-700 mr-2 space-y-0.5 py-1">
            {children_block}
          </div>
        </div>'''

        return folder_html, any_child_changed

    # Build root children
    root_children_html = []
    for idx, child in enumerate(tree_data.get("children", [])):
        c_html, _ = render_node(child, "root", idx)
        root_children_html.append(c_html)

    body_content = "".join(root_children_html)

    html_template = f'''<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
  <meta charset="UTF-8">
  <title>{html.escape(task_title)}</title>
  <script src="https://www.gstatic.com/antigravity/web/dev/tailwindcss.min.js"></script>
  <style>
    :root {{
      color-scheme: light dark;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: transparent;
      color: var(--foreground, #0f172a);
      margin: 0;
      padding: 10px;
      box-sizing: border-box;
    }}
    .tree-node {{
      user-select: none;
      transition: background-color 0.15s ease;
    }}
    .tree-node:hover {{
      background-color: rgba(148, 163, 184, 0.12);
    }}
    .badge-modified {{
      background-color: #FEF3C7;
      color: #92400E;
      border: 1px solid #FCD34D;
    }}
    .badge-new {{
      background-color: #ECFDF5;
      color: #065F46;
      border: 1px solid #6EE7B7;
    }}
    .badge-deleted {{
      background-color: #FEE2E2;
      color: #991B1B;
      border: 1px solid #FCA5A5;
    }}
    @media (prefers-color-scheme: dark) {{
      .badge-modified {{
        background-color: rgba(217, 119, 6, 0.2);
        color: #FBBF24;
        border-color: rgba(245, 158, 11, 0.35);
      }}
      .badge-new {{
        background-color: rgba(16, 185, 129, 0.2);
        color: #34D399;
        border-color: rgba(16, 185, 129, 0.35);
      }}
      .badge-deleted {{
        background-color: rgba(239, 68, 68, 0.2);
        color: #F87171;
        border-color: rgba(239, 68, 68, 0.35);
      }}
    }}
  </style>
</head>
<body>
  <div class="border border-slate-300 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-900 shadow-sm overflow-hidden text-sm">
    <!-- Header -->
    <div class="p-3 bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
      <div class="flex items-center gap-2">
        <span class="font-bold text-slate-800 dark:text-slate-100">{html.escape(task_title)}</span>
        <span class="text-xs px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-300 font-mono">job_search_automation</span>
      </div>
      <div class="flex items-center gap-3 text-xs">
        <span class="flex items-center gap-1 font-medium text-amber-700 dark:text-amber-400">{mod_count} עודכנו</span>
        <span class="flex items-center gap-1 font-medium text-emerald-700 dark:text-emerald-400">{add_count} נוספו</span>
        <span class="flex items-center gap-1 font-medium text-rose-700 dark:text-rose-400">{del_count} הוסרו</span>
        <button id="toggleAllBtn" class="px-2 py-1 bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600 rounded text-xs transition">פתח הכל</button>
      </div>
    </div>

    <!-- Tree Content -->
    <div class="p-3 space-y-1 font-sans text-xs">
      {body_content}
    </div>
  </div>

  <script>
    function toggleFolder(id) {{
      const el = document.getElementById(id);
      const arrow = document.getElementById(id + '-arrow');
      if (!el) return;
      if (el.classList.contains('hidden')) {{
        el.classList.remove('hidden');
        if (arrow) arrow.textContent = '▼';
      }} else {{
        el.classList.add('hidden');
        if (arrow) arrow.textContent = '◀';
      }}
    }}

    let allExpanded = false;
    const toggleBtn = document.getElementById('toggleAllBtn');
    if (toggleBtn) {{
      toggleBtn.addEventListener('click', () => {{
        allExpanded = !allExpanded;
        document.querySelectorAll('[id$="-arrow"]').forEach(arrow => {{
          const targetId = arrow.id.replace('-arrow', '');
          const targetEl = document.getElementById(targetId);
          if (targetEl) {{
            if (allExpanded) {{
              targetEl.classList.remove('hidden');
              arrow.textContent = '▼';
            }} else {{
              targetEl.classList.add('hidden');
              arrow.textContent = '◀';
            }}
          }}
        }});
        toggleBtn.textContent = allExpanded ? 'כווץ הכל' : 'פתח הכל';
      }});
    }}
  </script>
</body>
</html>'''

    return html_template


def main() -> int:
    parser = argparse.ArgumentParser(description="Render interactive repository tree widget.")
    parser.add_argument("--output", "-o", type=str, help="Target HTML file path", default="")
    parser.add_argument("--title", "-t", type=str, help="Widget title header", default="עץ תיקיות פרויקט מעודכן")
    parser.add_argument("--depth", "-d", type=int, help="Directory scan depth", default=3)
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress stdout output")
    args = parser.parse_args()

    try:
        status_map, mod_count, add_count, del_count = get_git_status(REPO_ROOT)
        tree_data = build_tree_data(REPO_ROOT, max_depth=args.depth)
        html_out = generate_html_widget(
            tree_data=tree_data,
            status_map=status_map,
            mod_count=mod_count,
            add_count=add_count,
            del_count=del_count,
            task_title=args.title,
        )

        out_path = Path(args.output).resolve() if args.output else (REPO_ROOT / "docs" / "tree_widget.html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html_out, encoding="utf-8")

        if not args.quiet:
            print(f'<agent-embed src="file://{out_path}"></agent-embed>')
            print(f"[OK] Tree widget rendered successfully: {out_path} ({mod_count} modified, {add_count} added, {del_count} deleted)")
    except Exception as e:
        # Resilient fallback: never crash or block the caller
        if not args.quiet:
            print(f"[WARN] Failed to render HTML tree widget: {e}", file=sys.stderr)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
