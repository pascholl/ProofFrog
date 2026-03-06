"""Tests for the canonicalization trace / divergence / step-after-transform tools."""

import copy
import io
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest

from proof_frog.web_server import (
    _capture_canonicalization_trace,
    _capture_divergence_point,
    _capture_step_after_transform,
    _setup_engine_for_proof,
)
from proof_frog import proof_engine, frog_ast

REPO_ROOT = Path(__file__).parent.parent
EXAMPLES = REPO_ROOT / "examples"
# A simple proof with multiple steps that all pass
PROOF_PATH = str(EXAMPLES / "Proofs" / "SymEnc" / "OTUCimpliesOTS.proof")


# -- _get_ast_manipulators --------------------------------------------------


def test_get_ast_manipulators_count() -> None:
    engine = proof_engine.ProofEngine(False)
    manipulators = engine._get_ast_manipulators()  # pylint: disable=protected-access
    assert len(manipulators) == 16
    # Each has a name and fn
    for m in manipulators:
        assert isinstance(m.name, str)
        assert callable(m.fn)


def test_get_ast_manipulators_names() -> None:
    engine = proof_engine.ProofEngine(False)
    manipulators = engine._get_ast_manipulators()  # pylint: disable=protected-access
    names = [m.name for m in manipulators]
    assert "Symbolic Computation" in names
    assert "Topological Sorting" in names
    assert "Remove unreachable blocks of code" in names


# -- canonicalize_game_with_trace -------------------------------------------


def test_trace_matches_canonicalize_game() -> None:
    """The traced version must produce the same canonical form."""
    suppress = io.StringIO()
    with redirect_stdout(suppress), redirect_stderr(suppress):
        engine, proof_file = _setup_engine_for_proof(
            PROOF_PATH, allowed_root=str(EXAMPLES)
        )
        step = proof_file.steps[0]
        assert isinstance(step, frog_ast.Step)
        # pylint: disable=protected-access
        game = engine._get_game_ast(step.challenger, step.reduction)
        # pylint: enable=protected-access
        canon_normal = engine.canonicalize_game(copy.deepcopy(game))
        canon_traced, trace = engine.canonicalize_game_with_trace(copy.deepcopy(game))
    assert str(canon_normal) == str(canon_traced)
    assert trace["converged"] is True


def test_trace_has_iterations() -> None:
    result = _capture_canonicalization_trace(
        PROOF_PATH, 0, allowed_root=str(EXAMPLES)
    )
    assert result["success"] is True
    assert result["converged"] is True
    assert result["total_iterations"] >= 1
    iterations = result["iterations"]
    assert isinstance(iterations, list)
    assert len(iterations) >= 1
    for it in iterations:
        assert "iteration" in it
        assert "transforms_applied" in it
        assert isinstance(it["transforms_applied"], list)


def test_trace_invalid_step() -> None:
    result = _capture_canonicalization_trace(
        PROOF_PATH, 999, allowed_root=str(EXAMPLES)
    )
    assert result["success"] is False


# -- get_divergence_point ---------------------------------------------------


def test_divergence_passing_hop() -> None:
    result = _capture_divergence_point(
        PROOF_PATH, 0, allowed_root=str(EXAMPLES)
    )
    assert result["success"] is True
    assert result["equivalent"] is True


def test_divergence_invalid_step() -> None:
    result = _capture_divergence_point(
        PROOF_PATH, 999, allowed_root=str(EXAMPLES)
    )
    assert result["success"] is False


# -- get_step_after_transform -----------------------------------------------


def test_step_after_valid_transform() -> None:
    result = _capture_step_after_transform(
        PROOF_PATH, 0, "Simplify Returns", allowed_root=str(EXAMPLES)
    )
    assert result["success"] is True
    assert isinstance(result["output"], str)
    assert "transform_applied" in result
    assert isinstance(result["available_transforms"], list)


def test_step_after_invalid_transform() -> None:
    result = _capture_step_after_transform(
        PROOF_PATH, 0, "Nonexistent Transform", allowed_root=str(EXAMPLES)
    )
    assert result["success"] is False
    assert "available_transforms" in result
    assert len(result["available_transforms"]) == 19  # 16 core + 3 standardization


def test_step_after_standardization_transform() -> None:
    result = _capture_step_after_transform(
        PROOF_PATH, 0, "Variable Standardizing", allowed_root=str(EXAMPLES)
    )
    assert result["success"] is True
    assert isinstance(result["output"], str)


def test_step_after_transform_invalid_step() -> None:
    result = _capture_step_after_transform(
        PROOF_PATH, 999, "Simplify Returns", allowed_root=str(EXAMPLES)
    )
    assert result["success"] is False
