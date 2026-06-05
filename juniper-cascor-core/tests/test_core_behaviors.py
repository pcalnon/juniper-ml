"""Behavioral coverage for candidate-core paths used by distributed workers."""

import pickle

import pytest

try:
    import torch

    _HAS_TORCH = True
except Exception:  # pragma: no cover
    _HAS_TORCH = False

requires_torch = pytest.mark.skipif(not _HAS_TORCH, reason="torch required for candidate-core")


@requires_torch
def test_activation_wrapper_round_trips_titlecase_softmax_through_pickle():
    """TitleCase module activations must stay usable after multiprocessing serialization."""
    from utils.activation import ActivationWithDerivative

    activation = ActivationWithDerivative(torch.nn.Softmax(dim=1))
    restored = pickle.loads(pickle.dumps(activation))

    x = torch.tensor([1.0, 2.0, 3.0])
    output = restored(x)

    assert torch.allclose(output, torch.softmax(x, dim=-1))
    assert torch.isclose(output.sum(), torch.tensor(1.0))


@requires_torch
def test_dataset_save_load_round_trips_tensors(tmp_path):
    """The torch.save/torch.load helper pair should round-trip real tensor payloads."""
    from utils.utils import load_dataset, save_dataset

    x = torch.tensor([[0.0, 1.0], [2.0, 3.0]], dtype=torch.float32)
    y = torch.tensor([[1.0, 0.0], [0.0, 1.0]], dtype=torch.float32)
    dataset_path = tmp_path / "candidate_dataset.pt"

    save_dataset(x, y, dataset_path)
    loaded_x, loaded_y = load_dataset(dataset_path)

    assert torch.equal(loaded_x, x)
    assert torch.equal(loaded_y, y)


@requires_torch
def test_candidate_unit_round_trips_through_pickle_and_preserves_forward_output():
    """CandidateUnit must remain executable after the worker serializes it."""
    from candidate_unit.candidate_unit import CandidateUnit

    candidate = CandidateUnit(
        CandidateUnit__activation_function=torch.nn.Tanh(),
        CandidateUnit__input_size=2,
        CandidateUnit__output_size=1,
        CandidateUnit__display_frequency=0,
        CandidateUnit__status_frequency=0,
        CandidateUnit__random_seed=7,
        CandidateUnit__sequence_max_value=2,
        CandidateUnit__random_value_scale=0.01,
        CandidateUnit__log_level_name="CRITICAL",
        CandidateUnit__candidate_index=3,
    )
    candidate.weights = torch.tensor([0.5, -0.25])
    candidate.bias = torch.tensor([0.1])
    x = torch.tensor([[2.0, 4.0], [1.0, -1.0]], dtype=torch.float32)

    expected = candidate.forward(x)
    restored = pickle.loads(pickle.dumps(candidate))

    assert restored.logger is not None
    assert torch.allclose(restored.forward(x), expected)


@requires_torch
def test_correlation_rejects_ambiguous_one_dimensional_output_against_multi_output_error():
    """Correlation validation should fail cleanly before tensor math sees incompatible shapes."""
    from candidate_unit.candidate_unit import CandidateUnit

    candidate = CandidateUnit(
        CandidateUnit__activation_function=torch.nn.Tanh(),
        CandidateUnit__input_size=2,
        CandidateUnit__output_size=1,
        CandidateUnit__display_frequency=0,
        CandidateUnit__status_frequency=0,
        CandidateUnit__random_seed=11,
        CandidateUnit__sequence_max_value=2,
        CandidateUnit__random_value_scale=0.01,
        CandidateUnit__log_level_name="CRITICAL",
    )

    output = torch.tensor([0.2, 0.4, 0.6], dtype=torch.float32)
    residual_error = torch.tensor(
        [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
        dtype=torch.float32,
    )

    with pytest.raises(ValueError, match="same number of features"):
        candidate._calculate_correlation(output=output, residual_error=residual_error)


@requires_torch
def test_correlation_rejects_scalar_tensors_before_batch_shape_check():
    """Scalar tensors should be rejected by validation rather than leaking an IndexError."""
    from candidate_unit.candidate_unit import CandidateUnit

    candidate = CandidateUnit(
        CandidateUnit__activation_function=torch.nn.Tanh(),
        CandidateUnit__input_size=1,
        CandidateUnit__output_size=1,
        CandidateUnit__display_frequency=0,
        CandidateUnit__status_frequency=0,
        CandidateUnit__random_seed=13,
        CandidateUnit__sequence_max_value=2,
        CandidateUnit__random_value_scale=0.01,
        CandidateUnit__log_level_name="CRITICAL",
    )

    with pytest.raises(ValueError, match="at least one dimension"):
        candidate._calculate_correlation(
            output=torch.tensor(0.2, dtype=torch.float32),
            residual_error=torch.tensor(1.0, dtype=torch.float32),
        )
