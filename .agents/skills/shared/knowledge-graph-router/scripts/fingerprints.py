from __future__ import annotations

import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
CONTRACT_SCRIPTS = ROOT / ".agents/skills/shared/factory-contracts/scripts"
if str(CONTRACT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CONTRACT_SCRIPTS))

from artifact_contracts import parse_frontmatter, source_fingerprint  # noqa: E402


def current_source_fingerprints(path: Path, repo_root: Path) -> frozenset[str]:
    values = {
        "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
        source_fingerprint(path, repo_root, "1.0"),
    }
    try:
        metadata, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        schema_version = metadata.get("schema_version")
        if isinstance(schema_version, str) and schema_version:
            values.add(source_fingerprint(path, repo_root, schema_version))
    except (OSError, UnicodeDecodeError, ValueError):
        pass
    return frozenset(values)
