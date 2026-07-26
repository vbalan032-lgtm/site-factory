from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / ".agents/skills/shared/factory-contracts/scripts"))

from stage_cli import run_artifact_stage

if __name__ == "__main__":
    raise SystemExit(
        run_artifact_stage(
            "BUILD_REPORT",
            "Stage 5 Full-page Build",
            ("built",),
            required_inputs=(
                ("PAGE_CONTRACT", ("contract_ready",)),
                ("CREATIVE_BLUEPRINT", ("creative_approved",)),
                ("PAGE_COPY", ("copy_ready", "assets_not_needed")),
            ),
            asset_gate=True,
        )
    )
