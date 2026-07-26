import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / ".agents/skills"
FAMILIES = ("webpage-factory", "loop-engine", "seo-factory", "geo-factory")
CHECKERS = (
    "shared/03-seo-reviewer/SKILL.md",
    "shared/brand-compliance-checker/SKILL.md",
    "shared/claims-proof-checker/SKILL.md",
    "shared/release-gate-checker/SKILL.md",
    "shared/visual-compliance-checker/SKILL.md",
)
BASE_SOURCES = (
    "PROJECT_MASTER_CONTEXT.md",
    "docs/BRAND_STYLE.md",
    "docs/PRODUCT_MAP.md",
    "docs/CLAIMS_AND_PROOFS.md",
    "docs/PERSONAS.md",
    "docs/SITEMAP.md",
)


def inputs_section(text: str) -> str:
    match = re.search(r"(?ms)^## Inputs\s*$\n(.*?)(?=^## |\Z)", text)
    return match.group(1) if match else ""


class ContextConsumerContractTests(unittest.TestCase):
    def consumer_paths(self):
        paths = []
        for family in FAMILIES:
            paths.extend(sorted((SKILLS / family).glob("*/SKILL.md")))
        paths.extend(SKILLS / relative for relative in CHECKERS)
        return paths

    def test_page_seo_geo_and_checkers_use_pack_as_the_only_context_entry(self):
        failures = []
        for path in self.consumer_paths():
            text = path.read_text(encoding="utf-8")
            if "context-pack-loader" not in text:
                failures.append(f"{path.relative_to(ROOT)}: missing context-pack-loader")
            if "exact_source_triggers" not in text:
                failures.append(f"{path.relative_to(ROOT)}: missing exact-source policy")
            inputs = inputs_section(text)
            for source in BASE_SOURCES:
                if source in inputs:
                    failures.append(
                        f"{path.relative_to(ROOT)}: unconditional input {source}"
                    )
        self.assertEqual(failures, [])

    def test_context_pack_is_stdout_json_and_never_a_tracked_artifact(self):
        text = (SKILLS / "shared/context-pack-loader/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("stdout", text)
        self.assertIn("JSON", text)
        self.assertIn("exact_source_triggers", text)
        self.assertRegex(text, r"(?i)do not (?:create|write).*(?:tracked|CONTEXT_PACK)")


if __name__ == "__main__":
    unittest.main()
