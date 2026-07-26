import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
ROOT = REPO_ROOT / "templates/nextjs"
COMPONENTS = ROOT / "components.json"
GLOBALS = ROOT / "app/globals.css"

SEMANTIC_TOKEN_MAP = {
    "background": "color-paper",
    "foreground": "color-text",
    "primary": "color-project-red",
    "primary-foreground": "color-on-primary",
    "secondary": "color-surface",
    "secondary-foreground": "color-text",
    "muted": "color-surface",
    "muted-foreground": "color-text-muted",
    "accent": "color-project-red-soft",
    "accent-foreground": "color-project-red-strong",
    "destructive": "color-project-red-strong",
    "border": "color-border",
    "input": "color-border-strong",
    "ring": "color-project-red",
    "radius": "radius-md",
}


def parse_css_variables(block: str) -> dict[str, str]:
    return dict(re.findall(r"--([\w-]+)\s*:\s*([^;]+);", block))


def find_variable_cycle(variables: dict[str, str]) -> list[str]:
    dependencies = {
        name: re.findall(r"var\(--([\w-]+)", value)
        for name, value in variables.items()
    }

    def visit(name: str, path: list[str]) -> list[str]:
        if name in path:
            return path[path.index(name) :] + [name]
        if name not in dependencies:
            return []
        for dependency in dependencies[name]:
            cycle = visit(dependency, [*path, name])
            if cycle:
                return cycle
        return []

    for variable in dependencies:
        cycle = visit(variable, [])
        if cycle:
            return cycle
    return []


class ShadcnFoundationTests(unittest.TestCase):
    def load_components(self) -> dict:
        self.assertTrue(COMPONENTS.is_file(), "components.json must exist")
        return json.loads(COMPONENTS.read_text(encoding="utf-8"))

    def test_components_json_matches_current_next_tailwind_project(self):
        config = self.load_components()

        self.assertTrue(config.get("rsc"), "Next App Router must use RSC mode")
        self.assertTrue(config.get("tsx"), "The project is TypeScript")
        self.assertEqual(config.get("style"), "base-nova")

        tailwind = config.get("tailwind", {})
        self.assertEqual(tailwind.get("config"), "")
        self.assertEqual(tailwind.get("css"), "app/globals.css")
        self.assertTrue(tailwind.get("cssVariables"))

    def test_aliases_resolve_inside_repository(self):
        config = self.load_components()
        aliases = config.get("aliases", {})
        expected = {
            "components": "@/components",
            "ui": "@/components/ui",
            "utils": "@/lib/utils",
            "lib": "@/lib",
            "hooks": "@/hooks",
        }
        self.assertEqual(aliases, expected)

        for alias in aliases.values():
            self.assertTrue(alias.startswith("@/"))
            resolved = (ROOT / alias.removeprefix("@/")).resolve()
            self.assertTrue(resolved.is_relative_to(ROOT.resolve()))

    def test_global_css_has_project_owned_semantic_tokens(self):
        css = GLOBALS.read_text(encoding="utf-8")
        root_blocks = re.findall(r":root\s*\{([^}]*)\}", css, flags=re.DOTALL)
        self.assertTrue(root_blocks, "globals.css must define :root tokens")
        theme = css.split("@theme inline", 1)[1].split("}", 1)[0]
        variables = {}
        for block in root_blocks:
            variables.update(parse_css_variables(block))

        for token, base_token in SEMANTIC_TOKEN_MAP.items():
            self.assertEqual(variables.get(token), f"var(--{base_token})")
            if token != "radius":
                self.assertIn(f"--color-{token}: var(--{token});", theme)

        self.assertEqual(find_variable_cycle(variables), [])

    def test_preset_does_not_replace_approved_project_typography(self):
        layout = (ROOT / "app/layout.tsx").read_text(encoding="utf-8")
        css = GLOBALS.read_text(encoding="utf-8")

        self.assertNotIn("next/font/google", layout)
        self.assertIn('<html lang="ru"', layout)
        self.assertIn("--font-sans: var(--font-sans-stack);", css)

    def test_foundation_adds_no_component_set(self):
        ui_dir = ROOT / "components/ui"
        self.assertTrue(ui_dir.is_dir())
        self.assertEqual(
            sorted(path.relative_to(ui_dir).as_posix() for path in ui_dir.rglob("*.tsx")),
            ["button.tsx"],
            "Task 5.5 may keep only the minimal button primitive from --defaults",
        )

    def test_lint_excludes_local_tool_scratch(self):
        eslint = (ROOT / "eslint.config.mjs").read_text(encoding="utf-8")
        self.assertIn('".tmp/**"', eslint)
        self.assertIn('".playwright-mcp/**"', eslint)

    def test_project_discovery_excludes_local_tool_scratch(self):
        tsconfig = json.loads((ROOT / "tsconfig.json").read_text(encoding="utf-8"))
        excluded = set(tsconfig.get("exclude", []))
        self.assertIn(".tmp", excluded)
        self.assertIn(".playwright-mcp", excluded)

        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("/.tmp/", gitignore)
        self.assertIn("/.playwright-mcp/", gitignore)


if __name__ == "__main__":
    unittest.main()
