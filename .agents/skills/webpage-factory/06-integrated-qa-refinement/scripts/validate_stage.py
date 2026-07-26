from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / ".agents/skills/shared/factory-contracts/scripts"))

from stage_cli import run_artifact_stage

if __name__ == "__main__":
    raise SystemExit(
        run_artifact_stage(
            "QA_REPORT",
            "Stage 6 Integrated QA and Refinement",
            ("qa_passed",),
            required_inputs=(
                ("PAGE_CONTRACT", ("contract_ready",)),
                ("CREATIVE_BLUEPRINT", ("creative_approved",)),
                ("PAGE_COPY", ("copy_ready", "assets_not_needed")),
                ("BUILD_REPORT", ("built",)),
            ),
            asset_gate=True,
        )
    )
