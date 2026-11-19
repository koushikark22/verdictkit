"""LLM fence: no LLM client in the verdict path. Core requirement 11.3.

Runs today (static AST scan) and on every commit. Fenced paths must exist so the test can
never pass vacuously.
"""
import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

FENCED = [
    ROOT / "core/src/verdictkit/custody",
    ROOT / "core/src/verdictkit/examiner",
    ROOT / "core/src/verdictkit/evidence",
    ROOT / "core/src/verdictkit/sweep.py",
    ROOT / "core/src/verdictkit/model.py",
    ROOT / "core/src/verdictkit/canonical.py",
    ROOT / "core/src/verdictkit/plugin.py",
    ROOT / "core/src/verdictkit/pipeline.py",
    ROOT / "core/src/verdictkit/bundle.py",
    ROOT / "core/src/verdictkit/api",
    ROOT / "core/src/verdictkit/cli.py",
    ROOT / "apps/reel-autopsy/src/reel_autopsy",
    ROOT / "apps/quote-autopsy/src/quote_autopsy",
]
ALLOWED_SUBPACKAGE = "assist"  # LLM-assisted drafting may live only in */assist/

BANNED_ROOTS = {
    "openai", "anthropic", "langchain", "langchain_core", "langchain_community", "litellm",
    "cohere", "mistralai", "transformers", "llama_index", "boto3", "botocore", "vertexai",
    "ollama", "groq", "together",
}
BANNED_DOTTED = {"google.generativeai", "google.genai", "google.cloud.aiplatform"}


def _python_files():
    for p in FENCED:
        if p.is_file():
            yield p
        else:
            for f in p.rglob("*.py"):
                if ALLOWED_SUBPACKAGE not in f.relative_to(p).parts:
                    yield f


def _banned(name: str) -> bool:
    return name.split(".")[0] in BANNED_ROOTS or any(
        name == d or name.startswith(d + ".") for d in BANNED_DOTTED
    )


def _violations(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if _banned(a.name):
                    yield node.lineno, a.name
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            if _banned(node.module):
                yield node.lineno, node.module
        elif isinstance(node, ast.Call):
            fn = node.func
            name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
            if name in {"import_module", "__import__"} and node.args:
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and _banned(arg.value):
                    yield node.lineno, arg.value


def test_fenced_paths_exist():
    missing = [str(p) for p in FENCED if not p.exists()]
    assert not missing, f"fenced paths missing: {missing}"


def test_fence_scans_real_files():
    assert sum(1 for _ in _python_files()) >= 20


@pytest.mark.parametrize("path", sorted(_python_files()), ids=lambda p: str(p.relative_to(ROOT)))
def test_no_llm_imports(path):
    found = list(_violations(path))
    assert not found, f"{path}: banned imports {found}"


def test_detector_catches_known_patterns(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text(
        "import openai\nfrom anthropic import Anthropic\nimport importlib\n"
        "importlib.import_module('litellm')\nfrom google.genai import types\n"
    )
    assert {n for _, n in _violations(bad)} == {"openai", "anthropic", "litellm", "google.genai"}
