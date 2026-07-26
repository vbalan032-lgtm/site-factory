from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


REQUIRED_FRONTMATTER = {
    "schema_version",
    "page_id",
    "route",
    "stage",
    "status",
    "source_fingerprints",
    "decisions",
    "unresolved_items",
    "approval",
    "next_stage_inputs",
}

ARTIFACT_RULES = {
    "PAGE_CONTRACT": (
        "stage-01-page-contract",
        {"draft", "contract_ready"},
    ),
    "CREATIVE_BLUEPRINT": (
        "stage-02-creative-blueprint",
        {"draft", "creative_approved"},
    ),
    "PAGE_COPY": (
        "stage-03-conversion-copy",
        {"draft", "copy_ready", "assets_not_needed"},
    ),
    "ASSET_MANIFEST": (
        "stage-04-page-assets",
        {"draft", "assets_ready"},
    ),
    "BUILD_REPORT": (
        "stage-05-full-page-build",
        {"draft", "built", "blocked"},
    ),
    "QA_REPORT": (
        "stage-06-integrated-qa-refinement",
        {"draft", "qa_passed", "blocked"},
    ),
}

ARTIFACT_FILENAMES = {
    "PAGE_CONTRACT": "PAGE_CONTRACT.md",
    "CREATIVE_BLUEPRINT": "CREATIVE_BLUEPRINT.md",
    "PAGE_COPY": "PAGE_COPY.md",
    "ASSET_MANIFEST": "ASSET_MANIFEST.md",
    "BUILD_REPORT": "BUILD_REPORT.md",
    "QA_REPORT": "QA_REPORT.md",
}

REQUIRED_HANDOFF_INPUTS = {
    "PAGE_CONTRACT": {"PAGE_CONTRACT.md"},
    "CREATIVE_BLUEPRINT": {"PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md"},
    "PAGE_COPY": {"PAGE_CONTRACT.md", "CREATIVE_BLUEPRINT.md", "PAGE_COPY.md"},
    "ASSET_MANIFEST": {
        "PAGE_CONTRACT.md",
        "CREATIVE_BLUEPRINT.md",
        "PAGE_COPY.md",
        "ASSET_MANIFEST.md",
    },
    "BUILD_REPORT": {
        "PAGE_CONTRACT.md",
        "CREATIVE_BLUEPRINT.md",
        "PAGE_COPY.md",
        "BUILD_REPORT.md",
    },
    "QA_REPORT": {
        "PAGE_CONTRACT.md",
        "CREATIVE_BLUEPRINT.md",
        "PAGE_COPY.md",
        "BUILD_REPORT.md",
        "QA_REPORT.md",
    },
}

ACCEPTED_LATIN_TERMS = {
    "AI",
    "configured primary offer",
    "configured industry standard",
    "API",
    "Control",
    "configured domain method",
    "ERP",
    "domain method",
    "GEO",
    "IoT",
    "MES",
    "OpenGraph",
    "configured process method",
    "PLM",
    "Playwright",
    "QA",
    "Plan",
    "SCADA",
    "SEO",
    "SSR",
    "UI",
    "project",
    "UX",
}


def _parse_value(raw: str):
    value = raw.strip()
    if value.startswith(("{", "[", '"')):
        return json.loads(value)
    if value in {"true", "false"}:
        return value == "true"
    if value == "null":
        return None
    return value


def parse_frontmatter(text: str) -> tuple[dict, str]:
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise ValueError("artifact must start with YAML frontmatter delimiter")

    closing = normalized.find("\n---\n", 4)
    if closing < 0:
        raise ValueError("artifact frontmatter closing delimiter is missing")

    data = {}
    for line in normalized[4:closing].splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, raw = line.partition(":")
        if not separator:
            raise ValueError(f"invalid frontmatter line: {line}")
        data[key.strip()] = _parse_value(raw)

    return data, normalized[closing + 5 :]


def source_fingerprint(path: Path, repo_root: Path, schema_version: str) -> str:
    relative = path.resolve().relative_to(repo_root.resolve()).as_posix()
    digest = hashlib.sha256()
    digest.update(relative.encode("utf-8"))
    digest.update(b"\0")
    digest.update(path.read_bytes())
    digest.update(b"\0")
    digest.update(schema_version.encode("utf-8"))
    return f"sha256:{digest.hexdigest()}"


def validate_public_russian(
    text: str, accepted_terms: set[str] | tuple[str, ...] | list[str] | None = None
) -> list[str]:
    words = re.findall(r"[A-Za-z][A-Za-z0-9-]*", text)
    has_cyrillic = bool(re.search(r"[А-Яа-яЁё]", text))
    errors = []

    if words and not has_cyrillic:
        errors.append(
            "Публичный текст должен быть русскоязычным и использовать кириллицу."
        )

    allowed = set(ACCEPTED_LATIN_TERMS)
    if accepted_terms:
        for term in accepted_terms:
            allowed.update(re.findall(r"[A-Za-z][A-Za-z0-9-]*", term))
    unknown = sorted({word for word in words if word not in allowed})
    if has_cyrillic and unknown:
        errors.append(
            "Найдены непроверенные латинские слова: " + ", ".join(unknown[:10])
        )

    return errors


def validate_artifact(path: Path, expected_kind: str, repo_root: Path) -> list[str]:
    if expected_kind not in ARTIFACT_RULES:
        return [f"unknown artifact kind: {expected_kind}"]

    try:
        data, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]

    errors = []
    missing = sorted(REQUIRED_FRONTMATTER - data.keys())
    if missing:
        return ["missing frontmatter fields: " + ", ".join(missing)]

    expected_stage, valid_statuses = ARTIFACT_RULES[expected_kind]
    if data["stage"] != expected_stage:
        errors.append(f"expected stage {expected_stage}, got {data['stage']}")
    if data["status"] not in valid_statuses:
        errors.append(f"invalid {expected_kind} status: {data['status']}")
    if data["route"] != "/" and not str(data["route"]).startswith("/"):
        errors.append("route must start with /")
    if not isinstance(data["source_fingerprints"], dict):
        errors.append("source_fingerprints must be an object")
    if not isinstance(data["decisions"], list):
        errors.append("decisions must be a list")
    if not isinstance(data["unresolved_items"], list):
        errors.append("unresolved_items must be a list")
    if not isinstance(data["approval"], dict):
        errors.append("approval must be an object")
    if not isinstance(data["next_stage_inputs"], list):
        errors.append("next_stage_inputs must be a list")
    else:
        missing_handoff = sorted(
            REQUIRED_HANDOFF_INPUTS[expected_kind] - set(data["next_stage_inputs"])
        )
        if missing_handoff:
            errors.append(
                "next-stage handoff is missing required inputs: "
                + ", ".join(missing_handoff)
            )
    if not body.strip():
        errors.append("artifact body must not be empty")

    if expected_kind in {"PAGE_COPY", "QA_REPORT"}:
        configured_terms: list[str] = []
        config_path = repo_root / ".site-factory/project.json"
        if config_path.is_file():
            try:
                configured = json.loads(config_path.read_text(encoding="utf-8"))
                terms = configured.get("accepted_latin_terms", [])
                if isinstance(terms, list) and all(isinstance(term, str) for term in terms):
                    configured_terms = terms
            except (OSError, json.JSONDecodeError):
                pass
        errors.extend(validate_public_russian(body, configured_terms))

    return errors


def _decision_value(decisions: list, decision_id: str):
    for decision in decisions:
        if isinstance(decision, dict) and decision.get("id") == decision_id:
            return decision.get("value")
    return None


def is_mutable_implementation_evidence(
    artifact_kind: str, data: dict, source_name: str
) -> bool:
    """Allow Stage 1 implementation snapshots to change during the intended build.

    A page contract may inspect the existing route and components as migration
    evidence.  When the contract explicitly records ``preserve-not-freeze``, those
    snapshots prove what was reviewed but must not freeze the files that Stage 5
    is expected to replace.  Canonical business and technical sources remain
    fingerprint-strict.
    """

    if artifact_kind != "PAGE_CONTRACT":
        return False
    if (
        _decision_value(data.get("decisions", []), "implementation_evidence")
        != "preserve-not-freeze"
    ):
        return False

    parts = Path(source_name).parts
    return bool(parts) and parts[0] in {"app", "components", "pages", "src"}


def validate_completed_artifact(
    path: Path,
    expected_kind: str,
    repo_root: Path,
    expected_statuses: set[str],
) -> list[str]:
    errors = validate_artifact(path, expected_kind, repo_root)
    if errors:
        return errors

    data, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    expected_filename = ARTIFACT_FILENAMES[expected_kind]
    if path.name != expected_filename:
        errors.append(
            f"canonical artifact filename must be {expected_filename}, got {path.name}"
        )
    if data["status"] not in expected_statuses:
        errors.append(
            "invalid completion status: "
            f"expected {', '.join(sorted(expected_statuses))}, got {data['status']}"
        )

    fingerprints = data["source_fingerprints"]
    if not fingerprints:
        errors.append("completed artifact requires source fingerprints")
    else:
        root = repo_root.resolve()
        for source_name, recorded in fingerprints.items():
            if not isinstance(source_name, str) or not isinstance(recorded, str):
                errors.append("source fingerprint entries must map paths to strings")
                continue
            if source_name != Path(source_name).as_posix():
                errors.append(
                    f"source fingerprint path must be normalized repository-relative: {source_name}"
                )
                continue
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", recorded):
                errors.append(f"invalid source fingerprint format: {source_name}")
                continue
            source = (root / source_name).resolve()
            try:
                source.relative_to(root)
            except ValueError:
                errors.append(f"source fingerprint path escapes repository: {source_name}")
                continue
            if not source.is_file():
                errors.append(f"source fingerprint path does not exist: {source_name}")
                continue
            actual = source_fingerprint(source, root, str(data["schema_version"]))
            if actual != recorded and not is_mutable_implementation_evidence(
                expected_kind, data, source_name
            ):
                errors.append(f"source fingerprint mismatch: {source_name}")

    if expected_kind == "CREATIVE_BLUEPRINT" and data["status"] == "creative_approved":
        approval = data["approval"]
        if approval.get("scope") != "creative" or approval.get("state") != "approved":
            errors.append("creative_approved requires creative approval")

    if expected_kind == "PAGE_COPY" and data["status"] in {
        "copy_ready",
        "assets_not_needed",
    }:
        expected_body_hash = _decision_value(data["decisions"], "copy_body_sha256")
        actual_body_hash = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
        if expected_body_hash != actual_body_hash:
            errors.append("copy body fingerprint is missing or does not match")
        if (
            data["status"] == "assets_not_needed"
            and _decision_value(data["decisions"], "assets") != "not_needed"
        ):
            errors.append("assets_not_needed requires decision assets=not_needed")

    return errors
