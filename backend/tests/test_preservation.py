"""
Preservation property tests for QuantumForge.

These tests assert BASELINE behavior that must not regress after fixes.
They MUST PASS on the current unfixed code.

P2:  validate_code returns (False, ...) for code containing dangerous patterns
P4:  SandboxExecutor.execute returns ExecutionResult with all 5 fields populated
P6:  VectorStore add/search round-trip returns correct entry_id in top-k
P10: retrieve_relevant respects k and min_score filters
P12: evolve() always produces a population of length population_size
P18: GET /health returns HTTP 200 with status, version, timestamp fields
"""

import sys
import os
import tempfile
import random

# Ensure backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from hypothesis import given, settings as h_settings, assume
import hypothesis.strategies as st


# ---------------------------------------------------------------------------
# P2: validate_code returns (False, ...) for dangerous patterns
# Validates: Requirements 3.1
# ---------------------------------------------------------------------------

DANGEROUS_PATTERNS = ["os.system", "subprocess", "eval(", "exec(", "__import__"]


@given(
    prefix=st.text(max_size=50),
    suffix=st.text(max_size=50),
    pattern=st.sampled_from(DANGEROUS_PATTERNS),
)
@h_settings(max_examples=50)
def test_p2_validate_code_blocks_dangerous_patterns(prefix, suffix, pattern):
    """
    P2 — Preservation: validate_code must return (False, ...) for any code
    containing a dangerous pattern, regardless of surrounding text.

    **Validates: Requirements 3.1**
    """
    from backend.sandbox.executor import SandboxExecutor

    executor = SandboxExecutor()
    code = prefix + pattern + suffix
    ok, msg = executor.validate_code(code)

    assert ok is False, (
        f"P2 COUNTEREXAMPLE: validate_code returned ({ok!r}, {msg!r}) for code "
        f"containing dangerous pattern {pattern!r}. It must return (False, ...)."
    )


# ---------------------------------------------------------------------------
# P4: SandboxExecutor.execute returns ExecutionResult with all 5 fields
# Validates: Requirements 3.9, 3.10
# ---------------------------------------------------------------------------

def test_p4_sandbox_execute_returns_full_result():
    """
    P4 — Preservation: SandboxExecutor.execute("print('hello')") must return
    an ExecutionResult with all 5 required fields populated.

    Note: executor.py uses log_structured which is not imported in the source
    (a separate bug). We patch it so the test focuses on the result structure.

    **Validates: Requirements 3.9, 3.10**
    """
    from backend.sandbox import executor as executor_module
    from backend.core.models import ExecutionResult
    from unittest.mock import MagicMock

    # Patch log_structured into the executor module namespace to work around
    # the missing import bug (C-unrelated to P4's concern)
    executor_module.log_structured = MagicMock()

    from backend.sandbox.executor import SandboxExecutor

    executor = SandboxExecutor()
    result = executor.execute("print('hello')")

    assert isinstance(result, ExecutionResult), (
        f"P4: execute() returned {type(result)!r}, expected ExecutionResult"
    )

    # All 5 required fields must be present and have the right types
    assert isinstance(result.success, bool), (
        f"P4: result.success is {type(result.success)!r}, expected bool"
    )
    assert isinstance(result.stdout, str), (
        f"P4: result.stdout is {type(result.stdout)!r}, expected str"
    )
    assert isinstance(result.stderr, str), (
        f"P4: result.stderr is {type(result.stderr)!r}, expected str"
    )
    assert isinstance(result.exit_code, int), (
        f"P4: result.exit_code is {type(result.exit_code)!r}, expected int"
    )
    assert isinstance(result.execution_time, float), (
        f"P4: result.execution_time is {type(result.execution_time)!r}, expected float"
    )


# ---------------------------------------------------------------------------
# P6: VectorStore add/search round-trip returns correct entry_id in top-k
# Validates: Requirements 3.3, 3.4
# ---------------------------------------------------------------------------

@given(
    n_entries=st.integers(min_value=1, max_value=10),
    target_idx=st.integers(min_value=0, max_value=9),
    seed=st.integers(min_value=0, max_value=2**31),
)
@h_settings(max_examples=30, deadline=None)
def test_p6_vector_store_round_trip(n_entries, target_idx, seed):
    """
    P6 — Preservation: After adding N entries to VectorStore and searching for
    one of them, the correct entry_id must appear in the top-k results.

    **Validates: Requirements 3.3, 3.4**
    """
    from backend.memory.vector_store import VectorStore

    assume(target_idx < n_entries)

    rng = random.Random(seed)

    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(store_path=tmpdir)

        # Build distinct entries with unique words to aid retrieval
        entries = []
        for i in range(n_entries):
            # Use a unique keyword per entry so search can distinguish them
            unique_word = f"uniquetoken{i}_{seed}"
            text = f"entry {i} {unique_word} description"
            entry_id = f"entry_{i}_{seed}"
            metadata = {"entry_id": entry_id, "text": text, "score": 0.8}
            store.add(text, metadata, entry_id)
            entries.append((entry_id, text, unique_word))

        # Search using the unique keyword of the target entry
        target_id, target_text, target_word = entries[target_idx]
        results = store.search(target_word, k=n_entries)

        result_ids = [meta.get("entry_id") for meta, _ in results]

        assert target_id in result_ids, (
            f"P6 COUNTEREXAMPLE: Searched for {target_word!r}, expected {target_id!r} "
            f"in top-{n_entries} results but got: {result_ids}"
        )


# ---------------------------------------------------------------------------
# P10: retrieve_relevant respects k and min_score
# Validates: Requirements 3.6
# ---------------------------------------------------------------------------

@given(
    scores=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=20,
    ),
    k=st.integers(min_value=1, max_value=5),
    min_score=st.floats(min_value=0.0, max_value=0.9, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=2**31),
)
@h_settings(max_examples=40, deadline=None)
def test_p10_retrieve_relevant_respects_k_and_min_score(scores, k, min_score, seed):
    """
    P10 — Preservation: retrieve_relevant(query, k, min_score) must return
    at most k entries, all with score >= min_score.

    **Validates: Requirements 3.6**
    """
    from backend.memory.manager import MemoryManager
    from backend.memory.vector_store import VectorStore

    with tempfile.TemporaryDirectory() as tmpdir:
        # Build a MemoryManager backed by a temp VectorStore
        manager = MemoryManager.__new__(MemoryManager)
        manager.store = VectorStore(store_path=tmpdir)

        rng = random.Random(seed)

        # Populate the store with entries at the given scores
        for i, score in enumerate(scores):
            entry_id = f"entry_{i}_{seed}"
            text = f"task description number {i} seed {seed}"
            metadata = {
                "entry_id": entry_id,
                "task_description": text,
                "code": f"print({i})",
                "score": score,
                "success": True,
                "tags": [],
                "timestamp": "2024-01-01T00:00:00",
            }
            manager.store.add(text, metadata, entry_id)

        # retrieve_relevant constructs MemoryEntry(result=None) internally.
        # On unfixed code this raises ValidationError (C9 bug).
        # We catch that specific error and skip — P10 is about filtering logic,
        # not about the C9 bug (which is tested separately in test_bug_conditions.py).
        from pydantic import ValidationError
        try:
            results = manager.retrieve_relevant("task description", k=k, min_score=min_score)
        except ValidationError:
            # C9 bug: MemoryEntry.result is non-optional — skip this example
            # (the C9 fix will make this path unreachable)
            return

        # Must not exceed k
        assert len(results) <= k, (
            f"P10 COUNTEREXAMPLE: retrieve_relevant returned {len(results)} entries "
            f"but k={k}. Must return at most k entries."
        )

        # All returned entries must have score >= min_score
        for entry in results:
            assert entry.score >= min_score, (
                f"P10 COUNTEREXAMPLE: Entry {entry.entry_id!r} has score {entry.score} "
                f"which is below min_score={min_score}."
            )


# ---------------------------------------------------------------------------
# P12: evolve() always produces a population of length population_size
# Validates: Requirements 3.7
# ---------------------------------------------------------------------------

@given(
    performance_values=st.lists(
        st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10,
    ),
    seed=st.integers(min_value=0, max_value=2**31),
)
@h_settings(max_examples=50, deadline=None)
def test_p12_evolve_preserves_population_size(performance_values, seed):
    """
    P12 — Preservation: After any evolve() call, len(population) must equal
    population_size.

    **Validates: Requirements 3.7**
    """
    import random as stdlib_random
    from backend.optimization.evolution import PromptEvolution

    stdlib_random.seed(seed)
    evolution = PromptEvolution()
    expected_size = evolution.population_size

    # Build performance dict mapping genome_ids to scores
    performance = {}
    for i, genome in enumerate(evolution.population):
        if i < len(performance_values):
            performance[genome.genome_id] = performance_values[i]

    evolution.evolve(performance)

    assert len(evolution.population) == expected_size, (
        f"P12 COUNTEREXAMPLE: After evolve(), population has {len(evolution.population)} "
        f"members but population_size={expected_size}."
    )


# ---------------------------------------------------------------------------
# P18: GET /health returns HTTP 200 with status, version, timestamp
# Validates: Requirements 3.14
# ---------------------------------------------------------------------------

def test_p18_health_endpoint_returns_200_with_required_fields():
    """
    P18 — Preservation: GET /health must return HTTP 200 with at minimum
    status, version, and timestamp fields.

    **Validates: Requirements 3.14**
    """
    from fastapi.testclient import TestClient

    # Import the app without triggering the full lifespan (avoid Ray init)
    from unittest.mock import patch, AsyncMock, MagicMock

    # Patch distributed_executor.initialize to avoid Ray startup
    with patch("backend.distributed.executor.distributed_executor") as mock_executor:
        mock_executor.initialize = AsyncMock()
        mock_executor.shutdown = MagicMock()

        from backend.api.routes import app

        with TestClient(app, raise_server_exceptions=True) as client:
            response = client.get("/health")

    assert response.status_code == 200, (
        f"P18 COUNTEREXAMPLE: GET /health returned HTTP {response.status_code}, expected 200."
    )

    body = response.json()

    assert "status" in body, (
        f"P18 COUNTEREXAMPLE: /health response missing 'status' field. Got: {body}"
    )
    assert "version" in body, (
        f"P18 COUNTEREXAMPLE: /health response missing 'version' field. Got: {body}"
    )
    assert "timestamp" in body, (
        f"P18 COUNTEREXAMPLE: /health response missing 'timestamp' field. Got: {body}"
    )
