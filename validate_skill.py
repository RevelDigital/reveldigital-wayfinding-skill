#!/usr/bin/env python3
"""
Validate skill structure and SKILL.md frontmatter.

Usage:
    python scripts/validate_skill.py <path/to/skill-folder>
"""

import re
import sys
from pathlib import Path

import yaml


def validate_skill(skill_path):
    skill_path = Path(skill_path)

    if not skill_path.exists() or not skill_path.is_dir():
        return False, f"Skill directory not found: {skill_path}"

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return False, "SKILL.md not found"

    content = skill_md.read_text()
    if not content.startswith("---"):
        return False, "No YAML frontmatter found"

    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid frontmatter format"

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if not isinstance(frontmatter, dict):
            return False, "Frontmatter must be a YAML dictionary"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML in frontmatter: {e}"

    allowed = {"name", "description", "license", "allowed-tools", "metadata", "compatibility"}
    unexpected = set(frontmatter.keys()) - allowed
    if unexpected:
        return False, f"Unexpected frontmatter key(s): {', '.join(sorted(unexpected))}"

    if "name" not in frontmatter:
        return False, "Missing 'name' in frontmatter"
    if "description" not in frontmatter:
        return False, "Missing 'description' in frontmatter"

    name = str(frontmatter["name"]).strip()
    if not re.match(r"^[a-z0-9-]+$", name):
        return False, f"Name '{name}' must be kebab-case (lowercase, digits, hyphens)"
    if name.startswith("-") or name.endswith("-") or "--" in name:
        return False, f"Name '{name}' has invalid hyphen placement"
    if len(name) > 64:
        return False, f"Name too long ({len(name)} chars, max 64)"

    description = str(frontmatter.get("description", "")).strip()
    if "<" in description or ">" in description:
        return False, "Description cannot contain angle brackets"
    if len(description) > 1024:
        return False, f"Description too long ({len(description)} chars, max 1024)"

    return True, "Skill is valid!"


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/validate_skill.py <skill-folder>")
        sys.exit(1)

    valid, message = validate_skill(sys.argv[1])
    print(f"{'✅' if valid else '❌'} {message}")
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
