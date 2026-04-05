"""
Bug condition exploration tests for QuantumForge.

These tests assert the CORRECT (fixed) behavior.
They are EXPECTED TO FAIL on unfixed code — that failure confirms the bugs exist.

C1:  validate_code should allow open( (file I/O is legitimate)
C5:  SandboxExecutor cmd should NOT contain -m resource or -m time
C9:  MemoryEntry.result should be Optional (None should not raise ValidationError)
C14: PromptEvolution should retain >= 2 unique genomes after 10 evolve() calls
"""

import sys
import os

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from unittest.mock import patch


# ---------------------------------------------------------------------------
# C1: validate_code should allow open( — it is NOT a dangerous pattern
# ---------------------------------------------------------------------------

def test_c1_validate_code_allows_open():
    """
    C1 — Bug: open( is in the dangerous list, so legitimate file I/O code is rejected.
    Expected (fixed) behavior: validate_code returns (True, ...) for code that only uses open().
    This test FAILS on unfixed code because validate_code returns (False, ...).
    """
    from backend.sandbox.executor import SandboxExecutor

    executor = SandboxExecutor()
    code = 'with open("out.txt", "w") as f: f.write(result)'
    ok, msg = executor.validate_code(code)

    assert ok is True, (
        f"C1 COUNTEREXAMPLE: validate_code returned ({ok!r}, {msg!r}) for code containing open(. "
        "open( should NOT be treated as dangerous."
    )


# ---------------------------------------------------------------------------
# C5: SandboxExecutor cmd must NOT contain -m resource or -m time
# ---------------------------------------------------------------------------

def test_c5_sandbox_cmd_no_broken_flags():
    """
    C5 — Bug: cmd is built as ["python", "-u", "-m", "resource", "-m", "time", script_path],
    which is not a valid Python invocation.
    Expected (fixed) behavior: cmd == ["python", "-u", str(script_path)].
    This test FAILS on unfixed code because the cmd contains -m resource -m time.
    """
    import tempfile
    import subprocess
    from pathlib import Path
    from backend.sandbox.executor import SandboxExecutor

    executor = SandboxExecutor()

    captured_cmd = []

    original_popen = subprocess.Popen

    def mock_popen(cmd, **kwargs):
        captured_cmd.extend(cmd)
        # Raise immediately so we don't actually run anything
        raise RuntimeError("mock_stop")

    with patch("subprocess.Popen", side_effect=mock_popen):
        try:
            executor.execute("print('hello')")
        except RuntimeError:
            pass

    assert len(captured_cmd) > 0, "Popen was never called — test setup issue"

    assert "-m" not in captured_cmd or (
        "resource" not in captured_cmd and "time" not in captured_cmd
    ), (
        f"C5 COUNTEREXAMPLE: cmd = {captured_cmd}. "
        "cmd must not contain '-m resource' or '-m time'."
    )

    # Positive assertion: cmd should be exactly ["python", "-u", <script_path>]
    assert captured_cmd[0] == "python", f"Expected 'python', got {captured_cmd[0]!r}"
    assert captured_cmd[1] == "-u", f"Expected '-u', got {captured_cmd[1]!r}"
    assert len(captured_cmd) == 3, (
        f"C5 COUNTEREXAMPLE: cmd has {len(captured_cmd)} elements: {captured_cmd}. "
        "Expected exactly ['python', '-u', script_path]."
    )


# ---------------------------------------------------------------------------
# C9: MemoryEntry.result should be Optional — None must not raise ValidationError
# ---------------------------------------------------------------------------

def test_c9_memory_entry_result_optional():
    """
    C9 — Bug: MemoryEntry.result is typed as ExecutionResult (non-optional).
    Pydantic v2 raises ValidationError when result=None is passed.
    Expected (fixed) behavior: MemoryEntry(result=None) constructs without error.
    This test FAILS on unfixed code with a ValidationError.
    """
    from pydantic import ValidationError

    try:
        from backend.core.models import MemoryEntry
        entry = MemoryEntry(
            entry_id="x",
            task_description="t",
            code="c",
            result=None,
            score=0.5,
            tags=[],
        )
    except ValidationError as exc:
        pytest.fail(
            f"C9 COUNTEREXAMPLE: MemoryEntry(result=None) raised ValidationError: {exc}. "
            "result should be Optional[ExecutionResult] = None."
        )
    except Exception as exc:
        pytest.fail(f"C9: Unexpected exception: {exc}")


# ---------------------------------------------------------------------------
# C14: PromptEvolution must retain >= 2 unique genomes after 10 evolve() calls
# ---------------------------------------------------------------------------

def test_c14_evolution_diversity_preserved():
    """
    C14 — Bug: elite_count = max(1, population_size // 5) = 1 for population_size=5.
    After several evolve() calls all offspring share the single elite parent,
    collapsing the population to 1 unique genome_id.
    Expected (fixed) behavior: >= 2 distinct genome_ids remain after 10 generations.
    This test FAILS on unfixed code because the population collapses to 1 unique genome.
    """
    from backend.optimization.evolution import PromptEvolution

    # Use a fixed seed for reproducibility
    import random
    random.seed(42)

    evolution = PromptEvolution()
    assert evolution.population_size == 5, (
        f"Expected population_size=5 from settings, got {evolution.population_size}"
    )

    for i in range(10):
        # Build dummy performance data: give each genome a slightly different score
        performance = {
            g.genome_id: 0.5 + (i % 3) * 0.1
            for g in evolution.population
        }
        evolution.evolve(performance)

    unique_ids = set(g.genome_id for g in evolution.population)
    assert len(unique_ids) >= 2, (
        f"C14 COUNTEREXAMPLE: After 10 evolve() calls, population has only "
        f"{len(unique_ids)} unique genome_id(s): {unique_ids}. "
        "Population diversity collapsed — elite_count is too small."
    )
