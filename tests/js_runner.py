# -*- coding: utf-8 -*-
"""
Universal JavaScript Runner for Test Suites.
Supports:
1. macOS native JavaScriptCore (/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc)
2. Standalone jsc CLI in PATH
3. Node.js in PATH (standard on GitHub Actions runners, Linux, Windows, macOS)
If no JS engine is found, raises unittest.SkipTest gracefully instead of crashing.
"""

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

MAC_JSC = Path("/System/Library/Frameworks/JavaScriptCore.framework/Versions/Current/Helpers/jsc")


def get_js_engine():
    """
    Returns (engine_type, executable_path).
    engine_type is 'jsc' or 'node' or None.
    """
    # 1. macOS native JavaScriptCore
    if MAC_JSC.exists() and os.access(str(MAC_JSC), os.X_OK):
        return ("jsc", str(MAC_JSC))

    # 2. Standalone jsc CLI in PATH
    which_jsc = shutil.which("jsc")
    if which_jsc:
        return ("jsc", which_jsc)

    # 3. Node.js in PATH (standard on GitHub Actions Ubuntu runners)
    which_node = shutil.which("node") or shutil.which("nodejs")
    if not which_node:
        for fallback in ["/usr/local/bin/node", "/opt/homebrew/bin/node", "/usr/bin/node"]:
            if os.path.isfile(fallback) and os.access(fallback, os.X_OK):
                which_node = fallback
                break

    if which_node:
        return ("node", which_node)

    return (None, None)


def has_js_runtime() -> bool:
    engine, _ = get_js_engine()
    return engine is not None


def skip_if_no_js(test_case: unittest.TestCase):
    if not has_js_runtime():
        test_case.skipTest("No JavaScript runtime (jsc or node) available in this environment")


def run_js(script_source: str, cwd: str = None, timeout: int = 30) -> subprocess.CompletedProcess:
    """
    Runs a JavaScript source string using the detected engine (jsc or node).
    Raises unittest.SkipTest if no JS engine is installed.
    """
    engine, exe = get_js_engine()
    if not engine:
        raise unittest.SkipTest("No JavaScript runtime (jsc or node) available in this environment.")

    # Universal shims ensuring uniform behavior in both JSC and Node.js
    shim = """
    if (typeof print === 'undefined') {
        globalThis.print = function() { console.log.apply(console, arguments); };
    }
    if (typeof quit === 'undefined') {
        globalThis.quit = function(code) { 
            if (typeof process !== 'undefined' && process.exit) {
                process.exit(code);
            }
        };
    }
    if (typeof load === 'undefined' && typeof require !== 'undefined') {
        var fs = require('fs');
        var vm = require('vm');
        globalThis.load = function(filePath) {
            var code = fs.readFileSync(filePath, 'utf8');
            vm.runInThisContext(code);
        };
    }
    """
    full_code = shim + "\n" + script_source

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", encoding="utf-8", delete=False) as tf:
        tf.write(full_code)
        temp_path = tf.name

    try:
        proc = subprocess.run(
            [exe, temp_path],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        return proc
    finally:
        try:
            os.unlink(temp_path)
        except Exception:
            pass
