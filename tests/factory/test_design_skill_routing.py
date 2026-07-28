import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "templates/nextjs"
ROUTING_POLICY = TEMPLATE / "docs/system/DESIGN_SKILL_ROUTING.md"

EXPECTED_DESIGN_ROUTING = {
    "website-design-system": (
        "shadcn",
        "ui-ux-pro-max",
        "design-taste-frontend",
    ),
    "02-creative-blueprint": (
        "design-taste-frontend",
        "ui-ux-pro-max",
        "shadcn",
    ),
    "04-page-assets": ("canvas-design",),
    "05-full-page-build": (
        "shadcn",
        "vercel-react-best-practices",
        "context7",
    ),
    "06-integrated-qa-refinement": (
        "web-design-guidelines",
        "vercel-react-best-practices",
        "design-taste-frontend",
        "shadcn",
    ),
}

EXPECTED_INSTALLED_TREE_HASHES = {
    "shadcn": "8009303546706b6f943021165366149f01d43845a2c5ea71e257ca2bf8b9a936",
    "web-design-guidelines": "0dc822a092499c06d11ffd10bf28ae625e4e5112c8fcdf00ffa3c5d2785dfe0f",
    "canvas-design": "b6b1170d1ce8b7fb362bc340181ad89398cfbcd3d7c5c19c20402f61beafb25e",
    "vercel-react-best-practices": "a3d27584d3e8456fceff05042c837ebc7dfb6f77524113fdb27e1244ad0a496a",
}

EXPECTED_LOCK_ENTRIES = {
    "canvas-design": {
        "source": "anthropics/skills",
        "skillPath": "skills/canvas-design/SKILL.md",
        "computedHash": "4e8bbc31d3b159efdd32d31a63ba8cd5a44d84911e924c1f2c709c50cbcdd0ec",
    },
    "shadcn": {
        "source": "shadcn-ui/ui",
        "skillPath": "skills/shadcn/SKILL.md",
        "computedHash": "4f78ff7cd3a4f637b6fe30dbbab4a80a19dd63fa62d9352bed461ccfdbcbbf43",
    },
    "vercel-react-best-practices": {
        "source": "vercel-labs/agent-skills",
        "skillPath": "skills/react-best-practices/SKILL.md",
        "computedHash": "6b526d013e28073246a36f99b529bc43745d30832ecfa8217b359c34f260ca6b",
    },
    "web-design-guidelines": {
        "source": "vercel-labs/agent-skills",
        "skillPath": "skills/web-design-guidelines/SKILL.md",
        "computedHash": "d8e7d3afe37dcc8a97b99ffb5afdb4d0919ae0092ea8b68f44eb201f035e33ac",
    },
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def tree_hash(path: Path) -> str:
    records = []
    files = (item for item in path.rglob("*") if item.is_file())
    for file_path in sorted(files, key=lambda item: item.as_posix().lower()):
        relative = file_path.relative_to(path).as_posix()
        records.append(f"{relative}={hashlib.sha256(file_path.read_bytes()).hexdigest()}")
    return hashlib.sha256("\n".join(records).encode("utf-8")).hexdigest()


class DesignSkillRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = read(ROUTING_POLICY)

    def test_canonical_routing_policy_exists(self):
        self.assertTrue(
            ROUTING_POLICY.is_file(),
            "Task 5 must create docs/system/DESIGN_SKILL_ROUTING.md",
        )

    def test_exact_stage_ownership_matrix_is_documented(self):
        for owner, tools in EXPECTED_DESIGN_ROUTING.items():
            row = re.search(
                rf"(?m)^\|\s*`?{re.escape(owner)}`?\s*\|(?P<tools>.+)\|$",
                self.policy,
            )
            self.assertIsNotNone(row, f"missing routing row for {owner}")
            routed_tools = tuple(re.findall(r"`([^`]+)`", row.group("tools")))
            self.assertEqual(routed_tools, tools, f"wrong routing for {owner}")

    def test_specialist_boundaries_and_context_thrift_are_explicit(self):
        required = (
            "review-only",
            "conditional static art",
            "foundation or new archetype",
            "Do not load all design skills",
        )
        for term in required:
            self.assertIn(term, self.policy)

    def test_state_only_work_routes_to_no_design_tools(self):
        self.assertRegex(
            self.policy,
            r"(?is)state-only.{0,240}(?:none|no design tools)",
        )

    def test_compliance_and_approved_russian_copy_outrank_taste(self):
        self.assertRegex(
            self.policy,
            r"(?is)Stage 6.{0,500}(?:compliance|accessibility).{0,160}"
            r"(?:block|outrank).{0,160}taste",
        )

    def test_authority_precedence_separates_immutable_constraints_from_artifacts(self):
        authority = self.policy.split("## Authority", 1)[1].split("## Ownership", 1)[0]
        tiers = (
            "direct owner instruction",
            "immutable brand core, claims discipline, Russian public-copy requirement, and technical/release constraints",
            "approved page artifacts and approved Creative Blueprint",
            "accessibility and web compliance",
            "framework and component contracts",
            "optional taste",
        )
        positions = [authority.find(tier) for tier in tiers]
        self.assertNotIn(-1, positions, "authority hierarchy must name every tier")
        self.assertEqual(positions, sorted(positions), "authority tiers are out of order")
        self.assertRegex(
            authority,
            r"(?is)Creative Blueprint.{0,240}(?:override|supersede).{0,160}visual baseline",
        )
        self.assertRegex(
            authority,
            r"(?is)Creative Blueprint.{0,320}(?:cannot|must not|never).{0,160}immutable",
        )
        self.assertRegex(
            self.policy,
            r"(?is)Russian.{0,160}approved artifacts.{0,160}"
            r"(?:outrank|override).{0,160}punctuation",
        )

    def test_local_nextjs_docs_precede_context7(self):
        self.assertRegex(
            self.policy,
            r"(?is)local Next\.js 16 docs.{0,200}(?:before|then).{0,120}Context7",
        )

    def test_owning_skills_use_their_scoped_routes(self):
        skill_routes = {
            ".agents/skills/website-factory/04-design-system-builder/SKILL.md": (
                "shadcn",
                "ui-ux-pro-max",
                "design-taste-frontend",
            ),
            ".agents/skills/webpage-factory/02-creative-blueprint/SKILL.md": (
                "design-taste-frontend",
                "ui-ux-pro-max",
                "shadcn",
            ),
            ".agents/skills/webpage-factory/04-page-assets/SKILL.md": (
                "canvas-design",
            ),
            ".agents/skills/webpage-factory/05-full-page-build/SKILL.md": (
                "shadcn",
                "vercel-react-best-practices",
                "Context7",
            ),
            ".agents/skills/webpage-factory/06-integrated-qa-refinement/SKILL.md": (
                "web-design-guidelines",
                "vercel-react-best-practices",
                "design-taste-frontend",
                "shadcn",
            ),
        }
        for relative_path, tools in skill_routes.items():
            text = read(ROOT / relative_path)
            for tool in tools:
                self.assertIn(tool, text, f"{relative_path} is missing {tool}")

    def test_context_pack_loader_is_graph_first_with_exact_file_safety(self):
        loader = read(ROOT / ".agents/skills/shared/context-pack-loader/SKILL.md")
        policy = read(TEMPLATE / "docs/system/SKILL_CONTEXT_POLICY.md")
        graph_position = loader.find("Use `knowledge-graph-router` first")
        exact_position = loader.find("returned exact evidence slices")
        fallback_position = loader.find("fall back only to existing files in `context_allowlist`")
        self.assertGreaterEqual(graph_position, 0)
        self.assertGreater(exact_position, graph_position)
        self.assertGreater(fallback_position, exact_position)
        self.assertRegex(
            policy,
            r"(?is)context-pack-loader.{0,800}exact_source_triggers.{0,800}"
            r"stage `context_allowlist`",
        )

    def test_agents_routes_v3_context_through_project_graph_first_entry(self):
        agents = read(TEMPLATE / "AGENTS.md")
        self.assertIn("project `context-pack-loader`", agents)
        self.assertIn("graph-first", agents)
        self.assertRegex(
            agents,
            r"(?is)global `context-loader`.{0,240}(?:compatibility|focused legacy)",
        )

    def test_website_factory_only_seeds_queue_then_routes_to_stage_1(self):
        planner = read(
            ROOT / ".agents/skills/website-factory/08-task-docs-planner/SKILL.md"
        )
        self.assertIn("foundation/task-contract maintainer", planner)
        self.assertIn("webpage-factory/01-page-contract", planner)
        self.assertNotIn("owned by `website-factory/08-task-docs-planner`", planner)

    def test_playwright_and_superpowers_have_precise_triggers(self):
        agents = read(TEMPLATE / "AGENTS.md")
        playwright_rules = (
            r"Stage 2.{0,120}optional reference/live-route inspection",
            r"Stage 5.{0,120}advisory smoke.{0,80}runnable page exists",
            r"Stage 6.{0,180}full-page desktop/mobile.{0,160}accessibility-tree.{0,120}SSR/SEO evidence",
            r"Stage 7.{0,120}staging smoke.{0,100}authorized",
            r"Do not run routine Playwright.{0,120}Stage 1.{0,80}Stage 3.{0,120}ordinary context reads.{0,80}state-only updates",
        )
        for rule in playwright_rules:
            self.assertRegex(agents, rf"(?is){rule}")

        superpower_triggers = {
            "superpowers:brainstorming": "unresolved creative/behavior design",
            "superpowers:writing-plans": "multi-step implementation planning",
            "superpowers:test-driven-development": "features and fixes",
            "superpowers:systematic-debugging": "unexpected failures",
            "superpowers:requesting-code-review": "substantial completed work",
            "superpowers:verification-before-completion": "before completion claims",
        }
        for skill, trigger in superpower_triggers.items():
            self.assertRegex(
                agents,
                rf"(?is){re.escape(skill)}.{{0,80}}{re.escape(trigger)}",
            )
        self.assertRegex(
            agents,
            r"(?is)full workflow.{0,100}not triggered.{0,100}ordinary copy.{0,80}"
            r"context reads.{0,80}state-only updates",
        )

    def test_brand_core_is_immutable_and_visual_baseline_is_evolvable(self):
        brand = read(TEMPLATE / "docs/BRAND_STYLE.md")
        agents = read(TEMPLATE / "AGENTS.md")
        for term in (
            "Неприкосновенное ядро",
            "Развиваемая визуальная база",
            "CREATIVE_BLUEPRINT.md",
            "benefit",
            "risk",
            "brand bridge",
            "русский кириллический текст",
        ):
            self.assertIn(term, brand + agents)

    def test_specialist_findings_return_to_v3_owner_stages(self):
        expected = {
            ".agents/skills/shared/claims-proof-checker/SKILL.md": ("Stage 1", "Stage 3"),
            ".agents/skills/shared/visual-compliance-checker/SKILL.md": ("Stage 2", "Stage 6"),
            ".agents/skills/shared/brand-compliance-checker/SKILL.md": ("Stage 2", "Stage 6"),
            ".agents/skills/shared/03-seo-reviewer/SKILL.md": ("Stage 3", "Stage 6"),
            ".agents/skills/shared/release-gate-checker/SKILL.md": ("Stage 7",),
        }
        for relative_path, stages in expected.items():
            text = read(ROOT / relative_path)
            for stage in stages:
                self.assertIn(stage, text, f"{relative_path} is missing {stage}")

    def test_triggered_seo_handoffs_do_not_route_to_webblock_production(self):
        for relative_path in (
            ".agents/skills/seo-factory/02-content-gap-finder/SKILL.md",
            ".agents/skills/seo-factory/05-faq-builder/SKILL.md",
        ):
            text = read(ROOT / relative_path)
            self.assertNotIn("webblock-factory/", text)
            self.assertIn("Stage 3", text)

    def test_task_5_does_not_initialize_shadcn_or_cross_task_5_5_boundary(self):
        policy = self.policy + read(TEMPLATE / "AGENTS.md")
        self.assertIn("Task 5.5", policy)
        self.assertNotIn("shadcn init", policy.lower())
        self.assertRegex(policy, r"components\.json.{0,100}Task 5\.5")

    def test_installed_skill_packages_and_lock_are_intact(self):
        lock = json.loads(read(ROOT / "skills-lock.json"))
        self.assertEqual(set(lock["skills"]), set(EXPECTED_LOCK_ENTRIES))
        for skill, expected_hash in EXPECTED_INSTALLED_TREE_HASHES.items():
            package = ROOT / ".agents/skills" / skill
            self.assertTrue((package / "SKILL.md").is_file())
            self.assertEqual(tree_hash(package), expected_hash, f"{skill} package changed")
            entry = lock["skills"][skill]
            self.assertEqual(entry["sourceType"], "github")
            for field, expected_value in EXPECTED_LOCK_ENTRIES[skill].items():
                self.assertEqual(entry[field], expected_value, f"wrong {field} for {skill}")

    def test_task_5_owned_active_files_have_no_stale_stage_routes(self):
        owned = (
            "AGENTS.md",
            "docs/system/SKILL_CONTEXT_POLICY.md",
            ".agents/skills/website-factory/04-design-system-builder/SKILL.md",
            ".agents/skills/website-factory/08-task-docs-planner/SKILL.md",
            ".agents/skills/webpage-factory/02-creative-blueprint/SKILL.md",
            ".agents/skills/webpage-factory/04-page-assets/SKILL.md",
            ".agents/skills/webpage-factory/05-full-page-build/SKILL.md",
            ".agents/skills/webpage-factory/06-integrated-qa-refinement/SKILL.md",
            ".agents/skills/shared/brand-compliance-checker/SKILL.md",
            ".agents/skills/shared/visual-compliance-checker/SKILL.md",
            ".agents/skills/shared/claims-proof-checker/SKILL.md",
            ".agents/skills/shared/03-seo-reviewer/SKILL.md",
            ".agents/skills/shared/context-pack-loader/SKILL.md",
            ".agents/skills/shared/release-gate-checker/SKILL.md",
            ".agents/skills/seo-factory/02-content-gap-finder/SKILL.md",
            ".agents/skills/seo-factory/05-faq-builder/SKILL.md",
        )
        stale_stage = re.compile(r"webpage-factory/(?:0[8-9]|1[0-8])-")
        for relative_path in owned:
            text = read(ROOT / relative_path)
            self.assertNotRegex(text, stale_stage, relative_path)
            for line in text.splitlines():
                if "webblock-factory/" in line:
                    self.assertRegex(
                        line,
                        r"(?i)migration evidence|focused repair",
                        relative_path,
                    )


if __name__ == "__main__":
    unittest.main()
