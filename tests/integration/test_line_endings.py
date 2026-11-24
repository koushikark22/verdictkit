"""Shell scripts must keep LF endings in every checkout (bash rejects CRLF; the container
entrypoint is copied from the working tree). Enforced by ``.gitattributes``."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_shell_scripts_are_lf_pinned_and_lf_on_disk():
    assert "*.sh text eol=lf" in (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    scripts = [ROOT / "deploy/entrypoint.sh", ROOT / "scripts/ui_e2e.sh", ROOT / "scripts/gate_nov22.sh"]
    for script in scripts:
        assert b"\r" not in script.read_bytes(), script.relative_to(ROOT)
