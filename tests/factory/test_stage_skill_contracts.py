import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FACTORY = ROOT / ".agents/skills/webpage-factory"


class StageSkillContractTests(unittest.TestCase):
    def assert_skill_contract(self, stage: str, required_terms: list[str]):
        skill_path = FACTORY / stage / "SKILL.md"
        agent_path = FACTORY / stage / "agents/openai.yaml"
        text = skill_path.read_text(encoding="utf-8")
        agent = agent_path.read_text(encoding="utf-8")

        self.assertRegex(text, rf"(?m)^name:\s*{re.escape(stage)}$")
        description = re.search(r"(?m)^description:\s*(.+)$", text)
        self.assertIsNotNone(description)
        self.assertTrue(description.group(1).startswith("Use when"))
        self.assertLess(len(text.split()), 500)
        for term in required_terms:
            self.assertIn(term, text, f"{stage} is missing {term}")
        self.assertIn(f"${stage}", agent)

    def test_stage_01_page_contract_skill(self):
        self.assert_skill_contract(
            "01-page-contract",
            [
                "PAGE_CONTRACT.md",
                "source fingerprints",
                "claims",
                "CTA",
                "route",
                "context_allowlist",
                "contract_ready",
            ],
        )

    def test_stage_02_creative_blueprint_skill(self):
        self.assert_skill_contract(
            "02-creative-blueprint",
            [
                "CREATIVE_BLUEPRINT.md",
                "8-12",
                "3-6",
                "ui-ux-pro-max",
                "design-taste-frontend",
                "Playwright",
                "creative approval",
                "visual baseline",
            ],
        )

    def test_stage_03_conversion_copy_skill(self):
        self.assert_skill_contract(
            "03-conversion-copy",
            [
                "PAGE_COPY.md",
                "Russian Cyrillic",
                "metadata",
                "claims",
                "SEO",
                "GEO",
                "copy_ready",
            ],
        )

    def test_stage_04_page_assets_skill(self):
        self.assert_skill_contract(
            "04-page-assets",
            [
                "ASSET_MANIFEST.md",
                "assets_not_needed",
                "reuse",
                "SVG",
                "alt text",
                "assets_ready",
            ],
        )

    def test_stage_05_full_page_build_skill(self):
        self.assert_skill_contract(
            "05-full-page-build",
            [
                "BUILD_REPORT.md",
                "Next.js 16",
                "full page",
                "lint",
                "typecheck",
                "build",
                "Playwright",
                "canonical",
                "OpenGraph",
                "schema",
                "FAQ",
                "indexability",
            ],
        )

    def test_stage_06_integrated_qa_refinement_skill(self):
        self.assert_skill_contract(
            "06-integrated-qa-refinement",
            [
                "QA_REPORT.md",
                "full-page",
                "desktop",
                "mobile",
                "one refine-pass",
                "accessibility",
                "SEO/SSR",
                "Playwright",
                "rendered metadata",
                "do not weaken tests or CI",
            ],
        )

    def test_stage_07_release_growth_skill(self):
        self.assert_skill_contract(
            "07-release-growth",
            [
                "staging_prepare",
                "production_release",
                "growth_iteration",
                "production approval",
                "release history",
                "Playwright",
                "--from-status",
                "--to-status",
                "secrets",
                "append-only",
                "--approval-file",
                "--history-file",
                "--previous-history-size",
                "--previous-history-sha256",
                "--iteration-stage",
            ],
        )

    def test_context_pack_loader_is_project_stage_router(self):
        skill = (
            ROOT / ".agents/skills/shared/context-pack-loader/SKILL.md"
        ).read_text(encoding="utf-8")
        policy = ROOT / ".agents/skills/shared/factory-contracts/references/stage-context-policy.md"

        for term in [
            "project-level context router",
            "Stage 1",
            "artifact-first",
            "fingerprints",
            "context_allowlist",
            "migration_evidence",
            "soft token budget",
            "Russian Cyrillic",
        ]:
            self.assertIn(term, skill)
        self.assertTrue(policy.is_file())


if __name__ == "__main__":
    unittest.main()
