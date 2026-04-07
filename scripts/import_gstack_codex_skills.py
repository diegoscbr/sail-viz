#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROJECT_SKILLS_FILE = REPO_ROOT / "CLAUDE.md"
UPSTREAM_ROOT = Path.home() / ".claude" / "skills" / "gstack" / ".agents" / "skills"
OUTPUT_ROOT = REPO_ROOT / ".agents" / "skills"
MANIFEST_PATH = OUTPUT_ROOT / "gstack-manifest.json"

ALIASES = {
    "connect-chrome": "open-gstack-browser",
}

EXCLUSIONS = {
    "codex": "Upstream gstack skips /codex on the Codex host because the skill is a Claude wrapper around Codex itself.",
}


@dataclass(frozen=True)
class SkillSpec:
    command: str
    slug: str


def parse_project_skills(path: Path) -> list[SkillSpec]:
    text = path.read_text()
    skills: list[SkillSpec] = []

    for line in text.splitlines():
        match = re.match(r"^\s*-\s+`(/[^`]+)`\s*$", line)
        if not match:
            continue
        command = match.group(1)
        skills.append(SkillSpec(command=command, slug=command.removeprefix("/")))

    if not skills:
        raise SystemExit(f"No skills found in {path}")

    return skills


def extract_description(skill_md: Path) -> str:
    text = skill_md.read_text()
    match = re.search(
        r"^description:\s*\|\n(?P<body>(?:^[ ]{2}.*\n?)*)",
        text,
        re.MULTILINE,
    )
    if match:
        return "\n".join(line[2:] for line in match.group("body").splitlines()).strip()

    match = re.search(r"^description:\s*(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()

    return ""


def external_skill_dir_name(slug: str) -> str:
    if slug.startswith("gstack-"):
        return slug
    return f"gstack-{slug}"


def upstream_dir_for_slug(slug: str) -> Path:
    alias_target = ALIASES.get(slug, slug)
    return UPSTREAM_ROOT / external_skill_dir_name(alias_target)


def output_dir_for_slug(slug: str) -> Path:
    return OUTPUT_ROOT / external_skill_dir_name(slug)


def remove_if_exists(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def copy_skill_tree(src: Path, dst: Path) -> None:
    remove_if_exists(dst)
    shutil.copytree(src, dst)


def write_alias_skill(alias_slug: str, src: Path, dst: Path) -> None:
    remove_if_exists(dst)
    (dst / "agents").mkdir(parents=True, exist_ok=True)

    src_skill = (src / "SKILL.md").read_text()
    src_yaml = (src / "agents" / "openai.yaml").read_text()

    skill_text = src_skill.replace("open-gstack-browser", alias_slug)
    yaml_text = src_yaml.replace("gstack-open-gstack-browser", f"gstack-{alias_slug}")
    yaml_text = yaml_text.replace("open-gstack-browser", alias_slug)

    (dst / "SKILL.md").write_text(skill_text)
    (dst / "agents" / "openai.yaml").write_text(yaml_text)


def main() -> None:
    project_skills = parse_project_skills(PROJECT_SKILLS_FILE)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, object] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project_skills_file": str(PROJECT_SKILLS_FILE.relative_to(REPO_ROOT)),
        "source_root": str(UPSTREAM_ROOT),
        "output_root": str(OUTPUT_ROOT.relative_to(REPO_ROOT)),
        "runtime_root_written": False,
        "notes": [
            "This import writes repo-local Codex skill artifacts only: SKILL.md plus agents/openai.yaml.",
            "It does not vendor the full gstack runtime root. Generated skills continue to point at ~/.codex/skills/gstack unless a separate local runtime root is added later.",
        ],
        "skills": [],
    }

    missing: list[str] = []
    written = 0
    excluded = 0

    for spec in project_skills:
        entry: dict[str, object] = {
            "command": spec.command,
            "slug": spec.slug,
        }

        if spec.slug in EXCLUSIONS:
            entry["status"] = "excluded"
            entry["reason"] = EXCLUSIONS[spec.slug]
            manifest["skills"].append(entry)
            excluded += 1
            continue

        src_dir = upstream_dir_for_slug(spec.slug)
        dst_dir = output_dir_for_slug(spec.slug)

        entry["source_dir"] = str(src_dir)
        entry["target_dir"] = str(dst_dir.relative_to(REPO_ROOT))

        if not src_dir.is_dir():
            entry["status"] = "missing"
            entry["reason"] = f"Upstream Codex skill directory not found: {src_dir}"
            manifest["skills"].append(entry)
            missing.append(spec.slug)
            continue

        if spec.slug in ALIASES:
            write_alias_skill(spec.slug, src_dir, dst_dir)
            entry["status"] = "aliased"
            entry["alias_of"] = ALIASES[spec.slug]
        else:
            copy_skill_tree(src_dir, dst_dir)
            entry["status"] = "written"

        entry["description"] = extract_description(dst_dir / "SKILL.md")
        manifest["skills"].append(entry)
        written += 1

    manifest["counts"] = {
        "listed_in_project": len(project_skills),
        "written_or_aliased": written,
        "excluded": excluded,
        "missing": len(missing),
    }

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    if missing:
        missing_list = ", ".join(missing)
        raise SystemExit(f"Missing upstream skill directories for: {missing_list}")


if __name__ == "__main__":
    main()
