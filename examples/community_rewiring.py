"""Generic community-network rewiring example."""

from esdm.benchmarks import connectance_shift_world, pure_rewiring_world
from esdm.network import network_beta_q1, shared_taxon_rewiring_beta_q1


def main() -> None:
    before, after = pure_rewiring_world()
    rewiring = shared_taxon_rewiring_beta_q1(before, after)
    assert rewiring > 1.0

    high, low = connectance_shift_world()
    assert high.expected_connectance() > low.expected_connectance()
    assert network_beta_q1((high, low)) == 1.0

    print(f"shared-taxon rewiring beta: {rewiring:.3f}")
    print("scalar connectance shifts remain separate from rewiring")


if __name__ == "__main__":
    main()
