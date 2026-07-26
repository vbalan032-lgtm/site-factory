from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / ".agents/skills/shared/factory-contracts/scripts"))

from stage_cli import run_artifact_stage

if __name__ == "__main__":
    raise SystemExit(
        run_artifact_stage(
            "CREATIVE_BLUEPRINT",
            "Stage 2 Creative Blueprint",
            ("creative_approved",),
            required_inputs=(("PAGE_CONTRACT", ("contract_ready",)),),
        )
    )
