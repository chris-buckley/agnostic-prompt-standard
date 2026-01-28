from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = REPO_ROOT / "skill" / "agnostic-prompt-standard"
PLATFORMS_DIR = SKILL_ROOT / "platforms"
SCHEMA_PATH = PLATFORMS_DIR / "_schemas" / "platform-manifest.schema.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_platform_manifest_schema_requires_file_conventions() -> None:
    schema = _read_json(SCHEMA_PATH)
    required = schema.get("required")
    assert isinstance(required, list), "schema.required must be a list"
    assert "fileConventions" in required, (
        'schema.required must include "fileConventions"'
    )


def test_every_platform_manifest_includes_file_conventions() -> None:
    platform_dirs = [
        p for p in PLATFORMS_DIR.iterdir() if p.is_dir() and p.name != "_schemas"
    ]

    for platform_dir in platform_dirs:
        manifest_path = platform_dir / "manifest.json"
        assert manifest_path.exists(), f"Missing manifest.json in {platform_dir.name}"

        manifest = _read_json(manifest_path)
        fc = manifest.get("fileConventions")
        assert isinstance(fc, dict), (
            f'Platform "{platform_dir.name}" must define fileConventions'
        )

        instructions = fc.get("instructions")
        assert isinstance(instructions, list) and instructions, (
            f'Platform "{platform_dir.name}" must define fileConventions.instructions array'
        )


def test_schema_enforces_min_items_on_instructions() -> None:
    schema = _read_json(SCHEMA_PATH)
    ins = (
        schema.get("properties", {})
        .get("fileConventions", {})
        .get("properties", {})
        .get("instructions")
    )
    assert ins is not None, "Schema must define fileConventions.instructions"
    assert isinstance(ins.get("minItems"), int) and ins["minItems"] >= 1, (
        "Schema must enforce minItems >= 1 on instructions"
    )
