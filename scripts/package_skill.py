#!/usr/bin/env python3
"""
Package a skill folder into a distributable .skill file (ZIP archive).

Usage:
    python scripts/package_skill.py <path/to/skill-folder> [output-directory]
"""

import fnmatch
import sys
import zipfile
from pathlib import Path

EXCLUDE_DIRS = {"__pycache__", "node_modules"}
EXCLUDE_GLOBS = {"*.pyc"}
EXCLUDE_FILES = {".DS_Store"}
ROOT_EXCLUDE_DIRS = {"evals"}


def should_exclude(rel_path):
    parts = rel_path.parts
    if any(part in EXCLUDE_DIRS for part in parts):
        return True
    if len(parts) > 1 and parts[1] in ROOT_EXCLUDE_DIRS:
        return True
    name = rel_path.name
    if name in EXCLUDE_FILES:
        return True
    return any(fnmatch.fnmatch(name, pat) for pat in EXCLUDE_GLOBS)


def package_skill(skill_path, output_dir=None):
    skill_path = Path(skill_path).resolve()

    if not skill_path.is_dir():
        print(f"❌ Skill directory not found: {skill_path}")
        return None

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        print(f"❌ SKILL.md not found in {skill_path}")
        return None

    skill_name = skill_path.name
    out = Path(output_dir).resolve() if output_dir else Path.cwd()
    out.mkdir(parents=True, exist_ok=True)
    skill_file = out / f"{skill_name}.skill"

    try:
        with zipfile.ZipFile(skill_file, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp in skill_path.rglob("*"):
                if not fp.is_file():
                    continue
                arcname = fp.relative_to(skill_path.parent)
                if should_exclude(arcname):
                    print(f"  Skipped: {arcname}")
                    continue
                zf.write(fp, arcname)
                print(f"  Added:   {arcname}")

        print(f"\n✅ Packaged: {skill_file}")
        return skill_file

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/package_skill.py <skill-folder> [output-dir]")
        sys.exit(1)

    skill_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"📦 Packaging: {skill_path}\n")
    result = package_skill(skill_path, output_dir)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
