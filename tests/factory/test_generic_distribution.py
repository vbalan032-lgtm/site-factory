import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
# Opaque fingerprints keep the regression capable of detecting migrated
# customer vocabulary without embedding that customer's identity in the factory.
BANNED_FRAGMENT_FINGERPRINTS = {
    (6, "17d275d3ff7375df15b0d520cb8eb7701b380b72c33a9aeccf7cdb1e6f58d510"),
    (7, "79073b30874c20a31ddbc046fb553a38603d0d8c92ea87a61a2c8072dc1eeb88"),
    (4, "ad2f70c864e47c4b49f4ab0f72935b2c815ae3f613225d4fdf454027502060db"),
    (7, "b5533fc118d90fcf5bdd3083d2d8026b84c8d306053e0fe58ae0070552d5d748"),
    (4, "061758f2b2cc290405f5fd491ddddea513908929869ead5bae3e7dfeabca4131"),
    (13, "039d6add7ee0b6cf3cd97ffc914f663fa2e36f853824d8c4371c63f33b237d88"),
    (10, "8ff09c475dc48a3f9c162a3d63d1c7b33a679c9a7815d5a09c5991504cc487fa"),
    (10, "965f501bfbc9fc4c3945e8cde87b4a63cf8e92eb7b422b9bd0bf634ecc5e1436"),
    (11, "2c8c3c51efef16001bf21ef40b5926ebe8c2e8a15c4e1a728c93042357b6e2e7"),
}


class GenericDistributionTests(unittest.TestCase):
    def test_distribution_has_56_unique_active_skills(self):
        skill_files = sorted((ROOT / ".agents/skills").rglob("SKILL.md"))
        names = []
        for path in skill_files:
            match = re.search(
                r"(?m)^name:\s*['\"]?([^'\"\r\n]+)",
                path.read_text(encoding="utf-8"),
            )
            self.assertIsNotNone(match, path.as_posix())
            names.append(match.group(1).strip())

        self.assertEqual(len(skill_files), 56)
        self.assertEqual(len(names), len(set(names)))

    def test_distribution_contains_no_first_project_identity_or_personal_path(self):
        violations = []
        for path in ROOT.rglob("*"):
            excluded = {".git", ".tmp", ".runtime", ".next", "node_modules", "__pycache__", "dist"}
            relative_path = path.relative_to(ROOT)
            if not path.is_file() or any(part in excluded for part in relative_path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            relative = relative_path.as_posix()
            if re.search(r"(?i)[a-z]:[\\/]+users[\\/]+[^\\/\s]+", text):
                violations.append(f"{relative}: personal Windows path")
            for token in re.findall(r"(?iu)[\w.-]+", text.casefold()):
                for length, fingerprint in BANNED_FRAGMENT_FINGERPRINTS:
                    for start in range(max(0, len(token) - length + 1)):
                        fragment = token[start : start + length]
                        if hashlib.sha256(fragment.encode("utf-8")).hexdigest() == fingerprint:
                            violations.append(f"{relative}: customer vocabulary fingerprint")

        self.assertEqual(violations, [])

    def test_every_core_skill_routes_identity_and_paths_through_project_config(self):
        core_roots = (
            "website-factory",
            "webpage-factory",
            "seo-factory",
            "geo-factory",
            "loop-engine",
            "shared",
        )
        missing = []
        for root in core_roots:
            for path in (ROOT / ".agents/skills" / root).rglob("SKILL.md"):
                if ".site-factory/project.json" not in path.read_text(encoding="utf-8"):
                    missing.append(path.relative_to(ROOT).as_posix())

        self.assertEqual(missing, [])


if __name__ == "__main__":
    unittest.main()
