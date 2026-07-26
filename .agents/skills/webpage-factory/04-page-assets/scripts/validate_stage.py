from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / ".agents/skills/shared/factory-contracts/scripts"))

from stage_cli import run_artifact_stage

if __name__ == "__main__":
    raise SystemExit(
        run_artifact_stage(
            "ASSET_MANIFEST",
            "Stage 4 Page Assets",
            ("assets_ready",),
            required_inputs=(
                ("PAGE_CONTRACT", ("contract_ready",)),
                ("CREATIVE_BLUEPRINT", ("creative_approved",)),
                ("PAGE_COPY", ("copy_ready",)),
            ),
            allow_not_needed=True,
            not_needed_inputs=(
                ("PAGE_CONTRACT", ("contract_ready",)),
                ("CREATIVE_BLUEPRINT", ("creative_approved",)),
            ),
        )
    )
