#!/usr/bin/env python3
"""
Evolution Quality Gate Script
Usage: python scripts/evolution_gate.py <workspace_path>

Runs automated quality checks on evolution round changes.
Exit code 0 = PASS, 1 = FAIL (with failure reasons printed to stdout).

This script is called by the Architect in Phase 3 BEFORE calling
evolution_workspace(verdict="PASS"). If it fails, the round should
either be fixed or declared FAIL.
"""

import os
import sys
import subprocess
import py_compile
import json
import re


def get_changed_files(workspace: str) -> list[str]:
    """Get list of files changed in this evolution round via git diff."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True, text=True, cwd=workspace
        )
        if result.returncode == 0 and result.stdout.strip():
            return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except Exception:
        pass

    # Fallback: diff against the base branch
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--staged"],
            capture_output=True, text=True, cwd=workspace
        )
        if result.returncode == 0 and result.stdout.strip():
            return [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
    except Exception:
        pass

    # Last fallback: list all untracked + modified files
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=workspace
        )
        if result.returncode == 0 and result.stdout.strip():
            files = []
            for line in result.stdout.strip().split("\n"):
                if line.strip():
                    # Format: "XY filename" or "XY filename -> newname"
                    parts = line[3:].strip().split(" -> ")
                    files.append(parts[-1])
            return files
    except Exception:
        pass

    return []


PROTECTED_FILES = [
    "backend/llm/engine.py",
    "src/core/agent_wrapper.py",
    "src/tui/app.py",
    "src/tui/state.py",
    "src/tui/themes.py",
    "evolve.sh",
    "src/prompts/evolution_architect.md",
    "evolution_state.json",
    "README.md",
    "README_CN.md",
]

PROTECTED_DIRS = [
    "src/tui/screens/",
    "src/tui/components/",
    "src/tui/dialogs/",
]


def check_protected_files(changed_files: list[str]) -> list[str]:
    """Check that no protected files were modified."""
    violations = []
    for f in changed_files:
        normalized = f.replace("\\", "/")
        if normalized in PROTECTED_FILES:
            violations.append(f"PROTECTED FILE modified: {f}")
        for d in PROTECTED_DIRS:
            if normalized.startswith(d):
                violations.append(f"PROTECTED DIRECTORY modified: {f}")
                break
    return violations


def check_syntax(workspace: str, changed_files: list[str]) -> list[str]:
    """Compile-check all changed .py files."""
    errors = []
    py_files = [f for f in changed_files if f.endswith(".py")]
    for f in py_files:
        full_path = os.path.join(workspace, f)
        if not os.path.exists(full_path):
            continue  # Deleted file
        try:
            py_compile.compile(full_path, doraise=True)
        except py_compile.PyCompileError as e:
            errors.append(f"SYNTAX ERROR in {f}: {e}")
    return errors


def check_imports(workspace: str, changed_files: list[str]) -> list[str]:
    """Try importing each changed .py module to catch import errors."""
    errors = []
    py_files = [f for f in changed_files if f.endswith(".py") and not f.startswith("tests/")]

    for f in py_files:
        full_path = os.path.join(workspace, f)
        if not os.path.exists(full_path):
            continue  # Deleted file

        # Convert file path to module path
        module_path = f.replace("/", ".").replace("\\", ".").removesuffix(".py")

        try:
            result = subprocess.run(
                [sys.executable, "-c", f"import {module_path}"],
                capture_output=True, text=True,
                cwd=workspace,
                env={**os.environ, "PYTHONPATH": workspace},
                timeout=30
            )
            if result.returncode != 0:
                # Filter out optional dependency errors (browser_use, etc.)
                stderr = result.stderr.strip()
                if stderr and "ModuleNotFoundError" in stderr:
                    # Check if it's a guarded import (try/except)
                    with open(full_path, "r") as fh:
                        content = fh.read()
                    # Extract the missing module name
                    match = re.search(r"No module named '(\w+)'", stderr)
                    if match:
                        missing_mod = match.group(1)
                        # Check if the import is inside a try block
                        if f"import {missing_mod}" in content:
                            # Check if there's a try/except around it
                            lines = content.split("\n")
                            for i, line in enumerate(lines):
                                if f"import {missing_mod}" in line:
                                    # Look backwards for try:
                                    in_try = False
                                    for j in range(i - 1, max(i - 5, -1), -1):
                                        if "try:" in lines[j]:
                                            in_try = True
                                            break
                                    if in_try:
                                        continue  # Guarded import, OK
                    errors.append(f"IMPORT ERROR in {f}: {stderr.split(chr(10))[-1]}")
        except subprocess.TimeoutExpired:
            errors.append(f"IMPORT TIMEOUT in {f}: took >30s")
        except Exception as e:
            errors.append(f"IMPORT CHECK FAILED for {f}: {e}")
    return errors


def check_dual_entry_wiring(workspace: str, changed_files: list[str]) -> list[str]:
    """Check that new tools/middleware are wired into both main.py and agent_bridge.py."""
    warnings = []

    # Find new tool files
    new_tools = [f for f in changed_files
                 if f.startswith("backend/tools/") and f.endswith(".py")
                 and not f.endswith("__init__.py") and not f.endswith("base.py")]

    # Find new middleware files
    new_middlewares = [f for f in changed_files
                      if f.startswith("src/core/middlewares/") and f.endswith(".py")
                      and not f.endswith("__init__.py")]

    if not new_tools and not new_middlewares:
        return warnings

    # Read both entry points
    main_path = os.path.join(workspace, "main.py")
    bridge_path = os.path.join(workspace, "src/tui/agent_bridge.py")

    main_content = ""
    bridge_content = ""

    if os.path.exists(main_path):
        with open(main_path, "r") as f:
            main_content = f.read()
    if os.path.exists(bridge_path):
        with open(bridge_path, "r") as f:
            bridge_content = f.read()

    for tool_file in new_tools:
        # Extract class names from the file
        full_path = os.path.join(workspace, tool_file)
        if not os.path.exists(full_path):
            continue
        with open(full_path, "r") as f:
            content = f.read()

        classes = re.findall(r"class\s+(\w+)\s*\(", content)
        module_name = os.path.splitext(os.path.basename(tool_file))[0]

        for cls in classes:
            if cls.endswith("Tool"):
                in_main = cls in main_content or module_name in main_content
                in_bridge = cls in bridge_content or module_name in bridge_content

                if not in_main and not in_bridge:
                    warnings.append(f"NEW TOOL NOT WIRED: {cls} from {tool_file} — not found in main.py OR agent_bridge.py")
                elif not in_main:
                    warnings.append(f"MISSING WIRING: {cls} from {tool_file} — found in agent_bridge.py but NOT in main.py")
                elif not in_bridge:
                    warnings.append(f"MISSING WIRING: {cls} from {tool_file} — found in main.py but NOT in agent_bridge.py")

    for mw_file in new_middlewares:
        full_path = os.path.join(workspace, mw_file)
        if not os.path.exists(full_path):
            continue
        with open(full_path, "r") as f:
            content = f.read()

        classes = re.findall(r"class\s+(\w+)\s*\(", content)
        module_name = os.path.splitext(os.path.basename(mw_file))[0]

        for cls in classes:
            if cls.endswith("Middleware"):
                in_main = cls in main_content or module_name in main_content
                in_bridge = cls in bridge_content or module_name in bridge_content

                if not in_main and not in_bridge:
                    warnings.append(f"NEW MIDDLEWARE NOT WIRED: {cls} from {mw_file} — not found in main.py OR agent_bridge.py")
                elif not in_main:
                    warnings.append(f"MISSING WIRING: {cls} from {mw_file} — found in agent_bridge.py but NOT in main.py")
                elif not in_bridge:
                    warnings.append(f"MISSING WIRING: {cls} from {mw_file} — found in main.py but NOT in agent_bridge.py")

    return warnings


def check_tests(workspace: str, changed_files: list[str]) -> list[str]:
    """Run pytest on test files related to changed files."""
    errors = []

    # Find test files: either directly changed, or matching changed modules
    test_files = [f for f in changed_files if f.startswith("tests/") and f.endswith(".py")]

    # Also find test files for changed non-test modules
    for f in changed_files:
        if f.startswith("tests/") or not f.endswith(".py"):
            continue
        basename = os.path.splitext(os.path.basename(f))[0]
        # Common test file patterns
        for pattern in [f"tests/test_{basename}.py", f"tests/{basename}_test.py"]:
            full = os.path.join(workspace, pattern)
            if os.path.exists(full) and pattern not in test_files:
                test_files.append(pattern)

    if not test_files:
        return []  # No tests to run — not an error

    # Verify test files exist
    existing_tests = [f for f in test_files if os.path.exists(os.path.join(workspace, f))]
    if not existing_tests:
        return []

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest"] + existing_tests + ["-v", "--tb=short", "-q"],
            capture_output=True, text=True,
            cwd=workspace,
            env={**os.environ, "PYTHONPATH": workspace},
            timeout=120
        )
        if result.returncode != 0:
            # Extract failure summary
            output = result.stdout.strip()
            # Get last 20 lines for summary
            summary_lines = output.split("\n")[-20:]
            errors.append(
                f"PYTEST FAILED (exit code {result.returncode}):\n"
                + "\n".join(summary_lines)
            )
    except subprocess.TimeoutExpired:
        errors.append("PYTEST TIMEOUT: tests took >120s")
    except Exception as e:
        errors.append(f"PYTEST ERROR: {e}")

    return errors


def check_duplication(workspace: str, changed_files: list[str]) -> list[str]:
    """Check for potential duplication with existing modules."""
    warnings = []

    new_py = [f for f in changed_files
              if f.endswith(".py") and not f.startswith("tests/")
              and not f.endswith("__init__.py")]

    for f in new_py:
        full_path = os.path.join(workspace, f)
        if not os.path.exists(full_path):
            continue

        with open(full_path, "r") as fh:
            content = fh.read()

        # Extract class names
        classes = re.findall(r"class\s+(\w+)\s*\(", content)

        for cls in classes:
            # Search for similar class names in the codebase
            try:
                result = subprocess.run(
                    ["grep", "-rn", f"class {cls}", "--include=*.py",
                     "backend/", "src/"],
                    capture_output=True, text=True, cwd=workspace
                )
                if result.stdout.strip():
                    matches = [line for line in result.stdout.strip().split("\n")
                               if f not in line]  # Exclude the file itself
                    if matches:
                        warnings.append(
                            f"POTENTIAL DUPLICATION: class {cls} in {f} — "
                            f"similar name found in: {'; '.join(m.split(':')[0] for m in matches[:3])}"
                        )
            except Exception:
                pass

    return warnings


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/evolution_gate.py <workspace_path>")
        sys.exit(1)

    workspace = os.path.abspath(sys.argv[1])
    if not os.path.isdir(workspace):
        print(f"ERROR: Workspace not found: {workspace}")
        sys.exit(1)

    print(f"=== Evolution Quality Gate ===")
    print(f"Workspace: {workspace}")

    changed_files = get_changed_files(workspace)
    if not changed_files:
        print("WARNING: No changed files detected. Gate passes vacuously.")
        sys.exit(0)

    print(f"Changed files ({len(changed_files)}):")
    for f in changed_files:
        print(f"  - {f}")
    print()

    all_errors = []
    all_warnings = []

    # Check 1: Protected files
    print("[1/6] Checking protected files...")
    errors = check_protected_files(changed_files)
    all_errors.extend(errors)
    print(f"  {'FAIL' if errors else 'PASS'} ({len(errors)} violations)")

    # Check 2: Syntax
    print("[2/6] Checking syntax...")
    errors = check_syntax(workspace, changed_files)
    all_errors.extend(errors)
    print(f"  {'FAIL' if errors else 'PASS'} ({len(errors)} errors)")

    # Check 3: Imports
    print("[3/6] Checking imports...")
    errors = check_imports(workspace, changed_files)
    all_errors.extend(errors)
    print(f"  {'FAIL' if errors else 'PASS'} ({len(errors)} errors)")

    # Check 4: Dual entry wiring
    print("[4/6] Checking dual entry point wiring...")
    errors = check_dual_entry_wiring(workspace, changed_files)
    all_errors.extend(errors)
    print(f"  {'FAIL' if errors else 'PASS'} ({len(errors)} issues)")

    # Check 5: Run tests
    print("[5/6] Running pytest...")
    errors = check_tests(workspace, changed_files)
    all_errors.extend(errors)
    print(f"  {'FAIL' if errors else 'PASS'} ({len(errors)} failures)")

    # Check 6: Duplication (warning only, not blocking)
    print("[6/6] Checking for duplication...")
    warnings = check_duplication(workspace, changed_files)
    all_warnings.extend(warnings)
    print(f"  {'WARN' if warnings else 'PASS'} ({len(warnings)} warnings)")

    print()

    if all_warnings:
        print("=== WARNINGS (non-blocking) ===")
        for w in all_warnings:
            print(f"  WARNING: {w}")
        print()

    if all_errors:
        print("=== ERRORS (blocking) ===")
        for e in all_errors:
            print(f"  ERROR: {e}")
        print()
        print(f"GATE RESULT: FAIL ({len(all_errors)} errors, {len(all_warnings)} warnings)")
        sys.exit(1)
    else:
        print(f"GATE RESULT: PASS ({len(all_warnings)} warnings)")
        sys.exit(0)


if __name__ == "__main__":
    main()
