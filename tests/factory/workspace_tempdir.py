from contextlib import contextmanager
from pathlib import Path
import shutil
from uuid import uuid4


@contextmanager
def workspace_tempdir(root: Path):
    """Create a test directory that inherits managed-workspace ACLs on Windows."""
    root.mkdir(exist_ok=True)
    path = root / f"tmp-{uuid4().hex}"
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path)
