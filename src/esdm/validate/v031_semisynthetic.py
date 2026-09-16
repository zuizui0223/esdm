"""Pinned real-geometry semi-synthetic fixture for v0.3.1 Gate F.

The fixture uses station geometry and long-term precipitation values derived from NOAA
GHCN data as published in a pinned revision of the-pudding/data. Ecological parameters,
observation effort, and all record counts remain synthetic and are generated through the
same esdm graph used for fitting.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
import csv
import io
import math
import statistics

from esdm.domain import Grid
from esdm.model import Model
from esdm.observe import EffortField, PresenceOnly
from esdm.process import LinearSuitability


@dataclass(frozen=True, slots=True)
class V031SemiSyntheticManifest:
    source_repository: str
    source_commit: str
    source_path: str
    source_blob_sha: str
    source_license: str
    upstream_data_source: str
    upstream_rights_note: str
    station_rows: int
    doy_bins: tuple[int, ...]
    hour_bins: tuple[int, ...]
    heldout_block: str

    @property
    def pinned_raw_url(self) -> str:
        return (
            f"https://raw.githubusercontent.com/{self.source_repository}/"
            f"{self.source_commit}/{self.source_path}"
        )


V031_SEMISYNTHETIC_MANIFEST = V031SemiSyntheticManifest(
    source_repository="the-pudding/data",
    source_commit="3dcb0a80c838ff9503e3957d7e004a7f4b888b0a",
    source_path="rain/annual_precipitation.csv",
    source_blob_sha="40b2adc5bf8a44a8bc9a1cfc3f99fc91b9fae949",
    source_license="MIT (repository); underlying NOAA/Federal data are public domain in the US unless otherwise noted",
    upstream_data_source="NOAA/NCEI Global Historical Climatology Network Daily (GHCN-Daily)",
    upstream_rights_note=(
        "NCEI policy states NOAA/Federal environmental data are public domain in the "
        "United States; the derived source repository is MIT licensed."
    ),
    station_rows=120,
    doy_bins=(15, 75, 135, 195, 255, 315),
    hour_bins=(0, 6, 12, 18),
    heldout_block="east",
)


@dataclass(frozen=True, slots=True)
class SemiSyntheticStation:
    station_id: str
    latitude: float
    longitude: float
    average_precip: float
    state: str


@dataclass(frozen=True, slots=True)
class V031SemiSyntheticFixture:
    model: Model
    stations: tuple[SemiSyntheticStation, ...]
    covariates: Mapping[tuple[str, int, int], Mapping[str, float]]
    spatial_blocks: tuple[str, ...]
    block_by_space: Mapping[str, str]
    train_spaces: tuple[str, ...]
    heldout_spaces: tuple[str, ...]
    heldout_block: str
    generating_theta: Mapping[str, Mapping[str, float]]
    manifest: V031SemiSyntheticManifest

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "covariates",
            MappingProxyType(
                {key: MappingProxyType(dict(values)) for key, values in self.covariates.items()}
            ),
        )
        object.__setattr__(self, "block_by_space", MappingProxyType(dict(self.block_by_space)))
        object.__setattr__(
            self,
            "generating_theta",
            MappingProxyType(
                {name: MappingProxyType(dict(values)) for name, values in self.generating_theta.items()}
            ),
        )


def parse_station_csv(text: str, *, rows: int = 120) -> tuple[SemiSyntheticStation, ...]:
    """Parse the first ``rows`` data rows under the frozen source ordering."""

    n_rows = int(rows)
    if n_rows < 100:
        raise ValueError("semi-synthetic fixture requires at least 100 station rows")
    reader = csv.DictReader(io.StringIO(str(text)))
    required = {"id", "average", "latitude", "longitude", "state"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        raise ValueError("source CSV is missing required station geometry columns")
    output: list[SemiSyntheticStation] = []
    for row in reader:
        if len(output) >= n_rows:
            break
        station_id = str(row["id"]).strip()
        if not station_id:
            raise ValueError("station id must be non-empty")
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
        average = float(row["average"])
        if not all(math.isfinite(value) for value in (latitude, longitude, average)):
            raise ValueError("station geometry and precipitation must be finite")
        output.append(
            SemiSyntheticStation(
                station_id=station_id,
                latitude=latitude,
                longitude=longitude,
                average_precip=average,
                state=str(row["state"]).strip(),
            )
        )
    if len(output) != n_rows:
        raise ValueError(f"source CSV provided {len(output)} rows; expected {n_rows}")
    if len({row.station_id for row in output}) != len(output):
        raise ValueError("selected station IDs must be unique")
    return tuple(output)


def _standardize(values: tuple[float, ...]) -> tuple[float, ...]:
    mean = statistics.fmean(values)
    sd = statistics.pstdev(values)
    if not math.isfinite(sd) or sd <= 0.0:
        raise ValueError("fixture covariate must have positive finite variation")
    return tuple((value - mean) / sd for value in values)


def _spatial_block(longitude: float) -> str:
    # Fixed, interpretable longitude bands; east is fully held out.
    if longitude < -110.0:
        return "west"
    if longitude < -85.0:
        return "central"
    return "east"


def _effort_value(station: SemiSyntheticStation, doy: int, hour: int) -> float:
    """Nonlinear, spatially and temporally structured synthetic observation effort."""

    lat_rad = math.radians(station.latitude)
    lon_rad = math.radians(station.longitude)
    seasonal = math.cos(2.0 * math.pi * (float(doy) - 30.0) / 365.0)
    hour_effect = {0: -0.25, 6: 0.05, 12: 0.25, 18: -0.05}[int(hour)]
    log_effort = (
        1.25
        + 0.30 * math.sin(2.2 * lat_rad)
        + 0.22 * math.cos(1.7 * lon_rad)
        + 0.18 * seasonal
        + hour_effect
    )
    return math.exp(log_effort)


def build_v031_semisynthetic_fixture(
    source_csv_text: str,
    *,
    manifest: V031SemiSyntheticManifest = V031_SEMISYNTHETIC_MANIFEST,
) -> V031SemiSyntheticFixture:
    """Build the frozen Gate-F fixture from pinned-source CSV text."""

    stations = parse_station_csv(source_csv_text, rows=manifest.station_rows)
    spaces = tuple(station.station_id for station in stations)
    grid = Grid(space=spaces, doy=manifest.doy_bins, hour=manifest.hour_bins)

    precip_z = _standardize(tuple(station.average_precip for station in stations))
    lat_z = _standardize(tuple(station.latitude for station in stations))
    station_covariates = {
        station.station_id: {
            "precip_z": precip_z[index],
            "lat_z": lat_z[index],
        }
        for index, station in enumerate(stations)
    }
    covariates = {
        key: dict(station_covariates[key[0]])
        for key in grid.keys
    }
    effort = EffortField(
        {
            key: _effort_value(stations[spaces.index(key[0])], key[1], key[2])
            for key in grid.keys
        }
    )
    suitability = LinearSuitability(
        covariates=("precip_z", "lat_z"),
        intercept_parameter="intercept",
        coefficient_parameters={
            "precip_z": "beta_precip",
            "lat_z": "beta_lat",
        },
    )
    stream = PresenceOnly(
        name="semi_synthetic_records",
        effort=effort,
        informs=frozenset({"suitability"}),
        targets=frozenset({"sp"}),
    )
    model = Model(
        domain=grid,
        species={"sp": (suitability,)},
        streams=(stream,),
    )
    model.check_design()

    block_by_space = {
        station.station_id: _spatial_block(station.longitude)
        for station in stations
    }
    spatial_blocks = tuple(
        block for block in ("west", "central", "east") if block in set(block_by_space.values())
    )
    if manifest.heldout_block not in spatial_blocks:
        raise ValueError("frozen heldout block is absent from selected station geometry")
    train_spaces = tuple(
        space for space in spaces if block_by_space[space] != manifest.heldout_block
    )
    heldout_spaces = tuple(
        space for space in spaces if block_by_space[space] == manifest.heldout_block
    )
    if not train_spaces or not heldout_spaces:
        raise ValueError("semi-synthetic spatial split must contain train and heldout stations")

    return V031SemiSyntheticFixture(
        model=model,
        stations=stations,
        covariates=covariates,
        spatial_blocks=spatial_blocks,
        block_by_space=block_by_space,
        train_spaces=train_spaces,
        heldout_spaces=heldout_spaces,
        heldout_block=manifest.heldout_block,
        generating_theta={
            "sp": {
                "intercept": 1.0,
                "beta_precip": 0.55,
                "beta_lat": -0.25,
            }
        },
        manifest=manifest,
    )
