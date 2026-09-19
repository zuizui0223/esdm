"""Backend-neutral observation blocks shared by likelihood and simulation paths."""

from __future__ import annotations

from dataclasses import dataclass


def _clean_keys(raw_keys):
    cleaned = []
    for key in raw_keys:
        if not isinstance(key, tuple) or len(key) != 3:
            raise ValueError("observation block keys must be (space, doy, hour)")
        cleaned.append((str(key[0]), int(key[1]), int(key[2])))
    keys = tuple(cleaned)
    if len(set(keys)) != len(keys):
        raise ValueError("observation block keys must be unique")
    return keys


def _leading_length(values):
    shape = getattr(values, "shape", None)
    if shape is not None and len(shape) >= 1:
        return int(shape[0])
    try:
        return len(values)
    except TypeError as exc:
        raise TypeError("observation block values must expose a leading length") from exc


@dataclass(frozen=True, slots=True)
class PoissonObservationBlock:
    """One ordered Poisson observation vector with a static exposure mask."""

    name: str
    keys: tuple[tuple[str, int, int], ...]
    rates: object
    observed: object | None = None
    structural_exposure_mask: tuple[bool, ...] = ()

    def __post_init__(self) -> None:
        name = str(self.name).strip()
        if not name:
            raise ValueError("observation block name must be non-empty")
        keys = _clean_keys(self.keys)
        if _leading_length(self.rates) != len(keys):
            raise ValueError("rates must match observation block key count")
        if self.observed is not None and _leading_length(self.observed) != len(keys):
            raise ValueError("observed values must match observation block key count")
        mask = tuple(bool(value) for value in self.structural_exposure_mask)
        if len(mask) != len(keys):
            raise ValueError("structural exposure mask must match observation block key count")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "keys", keys)
        object.__setattr__(self, "structural_exposure_mask", mask)
