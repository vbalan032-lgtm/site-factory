from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / ".agents/skills/shared/factory-contracts/scripts"))

from stage_cli import run_artifact_stage

if __name__ == "__main__":
    raise SystemExit(
        run_artifact_stage(
            "PAGE_COPY",
            "Stage 3 Conversion Copy",
            ("copy_ready",),
            required_inputs=(
                ("PAGE_CONTRACT", ("contract_ready",)),
                ("CREATIVE_BLUEPRINT", ("creative_approved",)),
            ),
        )
    )
