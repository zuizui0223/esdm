import pytest

from esdm.domain import Grid, Partition, RefinementChain, StateSpace


def test_grid_is_space_doy_hour_product():
    grid = Grid(space=("s1", "s2"), doy=(1, 8), hour=(0, 12))
    contexts = tuple(grid.contexts())
    assert len(contexts) == 8
    assert contexts[0].space == "s1"
    assert contexts[-1].hour == 12


def test_grid_rejects_duplicate_or_invalid_coordinates():
    with pytest.raises(ValueError):
        Grid(space=("s1", "s1"), doy=(1,), hour=(0,))
    with pytest.raises(ValueError):
        Grid(space=("s1",), doy=(0,), hour=(0,))
    with pytest.raises(ValueError):
        Grid(space=("s1",), doy=(1,), hour=(24,))


def test_refinement_chain_requires_true_refinement():
    states = StateSpace(("absent", "vegetative", "flowering"))
    occurrence = Partition(
        "occurrence",
        {"absent": ("absent",), "present": ("vegetative", "flowering")},
    )
    phenostage = Partition(
        "phenostage",
        {
            "absent": ("absent",),
            "vegetative": ("vegetative",),
            "flowering": ("flowering",),
        },
    )
    chain = RefinementChain(states, (occurrence, phenostage))
    assert chain.finest.name == "phenostage"

    bad = Partition(
        "bad",
        {"mixed": ("absent", "flowering"), "veg": ("vegetative",)},
    )
    with pytest.raises(ValueError):
        RefinementChain(states, (occurrence, bad))
