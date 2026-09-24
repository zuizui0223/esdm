from esdm.observe import OccupancyCount, OccupiedPresenceOnly
from esdm.process import ColonizationExtinctionOccupancy


def test_v07_public_dynamic_exports_are_available_on_current_stack():
    assert OccupancyCount.__name__ == "OccupancyCount"
    assert OccupiedPresenceOnly.__name__ == "OccupiedPresenceOnly"
    assert ColonizationExtinctionOccupancy.__name__ == "ColonizationExtinctionOccupancy"
