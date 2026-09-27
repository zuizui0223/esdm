import pytest

from esdm.benchmarks import (
    connectance_shift_world,
    pure_rewiring_world,
    stable_network_world,
    taxon_turnover_network_world,
    transfer_null_network_world,
    transfer_positive_network_world,
)
from esdm.network import network_beta_q1, shared_taxon_rewiring_beta_q1
from esdm.transfer import community_log_score_gain


def test_stable_world_has_no_rewiring():
    a, b = stable_network_world()
    assert network_beta_q1((a, b)) == pytest.approx(1.0)
    assert shared_taxon_rewiring_beta_q1(a, b) == pytest.approx(1.0)


def test_pure_rewiring_world_changes_edges_not_taxa():
    a, b = pure_rewiring_world()
    assert a.taxa == b.taxa
    assert shared_taxon_rewiring_beta_q1(a, b) > 1.0


def test_connectance_shift_world_changes_connectance_without_rewiring():
    a, b = connectance_shift_world()
    assert a.expected_connectance() != pytest.approx(b.expected_connectance())
    assert shared_taxon_rewiring_beta_q1(a, b) == pytest.approx(1.0)


def test_taxon_turnover_world_keeps_shared_edge_structure_stable():
    a, b = taxon_turnover_network_world()
    assert set(a.taxa) != set(b.taxa)
    assert network_beta_q1((a, b)) > 1.0
    assert shared_taxon_rewiring_beta_q1(a, b) == pytest.approx(1.0)


def test_transfer_worlds_separate_positive_from_null_edge_information():
    positive = community_log_score_gain(transfer_positive_network_world())
    null = community_log_score_gain(transfer_null_network_world())
    assert positive.macro_gain > 0.0
    assert null.macro_gain == pytest.approx(0.0)
