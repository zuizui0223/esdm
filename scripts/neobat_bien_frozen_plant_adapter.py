"""Replay the existing CR/PA climate-only plant component, without bat outcomes.

Use as ``with FixedPlantComponent(frozen_root, plant_zip, raster_dir) as model``.
``predict(country, cells)`` returns ``(scores_by_cell, invalid_environment_cells)``.
``training_cells(country, taxon)`` exposes exact fit-cell membership in memory,
so the caller can exclude overlapping evaluation cells without altering a fit.

This is the 106-plant weak-shadow component, not ecological M3. Source plots,
cell identifiers, coefficients and individual predictions are never serialized
here. Heavy dependencies and original helpers are imported only on entry.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.metadata
import json
import numbers
import os
import pathlib
import subprocess
import sys
from contextlib import ExitStack, contextmanager


FROZEN_COMMIT = "d65817fcb3c39060ed544261c291d76a198299c6"
PLANT_ARCHIVE_SHA256 = "4275ed6b9847fa9fb81a9e353ec1b9de151592f7c369b19f6145129059726c8b"
FIXED106_SHA256 = "41c9fc0128df6d0f3753edf4b82f6b5b36c6975c8d7c644bae4e4fd3e5bdaac6"
COUNTRIES = ("CR", "PA")
ORIGINAL_PACKAGES = {
    "numpy": "2.2.6", "scikit-learn": "1.7.2",
    "rasterio": "1.4.3", "pyproj": "3.7.2",
}
CORE_PATHS = (
    "scripts/neobat_shadow_source_geography_51fold.py",
    "scripts/neobat_plant_country_crossfit_pilot.py",
    "scripts/neobat_plant_within_dataset_source_gate.py",
    "scripts/neobat_same_cell_source_support.py",
    "scripts/neobat_gbif_full_source_qc.py",
    "scripts/neobat_worldclim_source_preflight.py",
    "scripts/neobat_spatial_cell_pilot.py",
)


def _read(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def _sha256(path):
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@contextmanager
def _working_directory(path):
    previous = pathlib.Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _training_rows_with_cells(source_rows, country_cells, country, taxon):
    """Retain cell IDs for exactly the rows selected by original plant_fit_rows.

    A cell can be represented under more than one training source-country;
    preserve those rows for count equality, but training_cells returns a set.
    """
    excluded = country_cells.get(country, set())
    return [row for region, rows in source_rows[taxon].items()
            if region != country for row in rows if row[0] not in excluded]


class FixedPlantComponent:
    """One context loads sources and fits all 106 plants for both CR and PA.

    Fitting finishes before this object accepts any external evaluation cells.
    The wrapper reuses the original scaler, classifier and fit-selection code.
    It neither changes source membership nor supplies BIEN labels to training.
    """

    def __init__(self, frozen_root, archive_path, raster_dir):
        self.frozen_root = pathlib.Path(frozen_root).resolve()
        self.archive_path = pathlib.Path(archive_path).resolve()
        self.raster_dir = pathlib.Path(raster_dir).resolve()
        self.taxa = ()
        self._stack = None
        self._models = {}
        self._source_rows = {}
        self._country_cells = {}
        self._environment = {}
        self._fit_records = []
        self._metadata = {}
        self._entered = False
        self._used = False

    def _git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.frozen_root), *args],
            check=True, capture_output=True, text=True,
        ).stdout.strip()

    def _verify_checkout(self):
        if self._git("rev-parse", "HEAD") != FROZEN_COMMIT:
            raise RuntimeError("FROZEN_PLANT_COMPONENT_COMMIT_MISMATCH")
        changed = self._git("diff", "--name-only", FROZEN_COMMIT, "--",
                            "scripts", "docs/replication/neobat")
        if changed:
            raise RuntimeError("FROZEN_PLANT_COMPONENT_TRACKED_INPUT_CHANGED")
        return {
            path: {"git_blob_sha": self._git("rev-parse", f"{FROZEN_COMMIT}:{path}"),
                   "sha256": _sha256(self.frozen_root / path)}
            for path in CORE_PATHS
        }

    def _import_original_helpers(self):
        """Add the immutable checkout to the existing scripts namespace."""
        root = str(self.frozen_root)
        original_scripts = str(self.frozen_root / "scripts")
        old_bytecode = sys.dont_write_bytecode
        sys.dont_write_bytecode = True
        sys.path.insert(0, root)
        scripts_package = sys.modules.get("scripts")
        old_package_path = None
        try:
            if scripts_package is not None:
                if not hasattr(scripts_package, "__path__"):
                    raise RuntimeError("SCRIPTS_IMPORT_NAMESPACE_COLLISION")
                old_package_path = scripts_package.__path__
                scripts_package.__path__ = [original_scripts, *list(old_package_path)]
            self._shadow = importlib.import_module("scripts.neobat_shadow_source_geography_51fold")
            self._plant = importlib.import_module("scripts.neobat_plant_country_crossfit_pilot")
            self._source = importlib.import_module("scripts.neobat_same_cell_source_support")
            self._names = importlib.import_module("scripts.neobat_gbif_full_source_qc")
            self._psource = importlib.import_module("scripts.neobat_plant_within_dataset_source_gate")
            for name, module in list(sys.modules.items()):
                if name.startswith("scripts.neobat_") and name != __name__:
                    location = getattr(module, "__file__", None)
                    # Only helpers owned by the old checkout are used here.
                    if name in {"scripts.neobat_shadow_source_geography_51fold",
                                "scripts.neobat_plant_country_crossfit_pilot",
                                "scripts.neobat_same_cell_source_support",
                                "scripts.neobat_gbif_full_source_qc",
                                "scripts.neobat_plant_within_dataset_source_gate"}:
                        if not location or not pathlib.Path(location).resolve().is_relative_to(self.frozen_root):
                            raise RuntimeError("FROZEN_PLANT_COMPONENT_IMPORT_PATH_MISMATCH")
        finally:
            sys.path.remove(root)
            if old_package_path is not None:
                scripts_package.__path__ = old_package_path
            sys.dont_write_bytecode = old_bytecode

    def __enter__(self):
        if self._used:
            raise RuntimeError("FROZEN_PLANT_COMPONENT_CONTEXT_ALREADY_USED")
        self._used = True
        self._stack = ExitStack()
        try:
            code_sources = self._verify_checkout()
            archive_sha = _sha256(self.archive_path)
            if archive_sha != PLANT_ARCHIVE_SHA256:
                raise RuntimeError("ORIGINAL_PLANT_ZIP_SHA_DRIFT")
            self._import_original_helpers()
            d = self.frozen_root / "docs/replication/neobat"
            # Only this helper uses relative receipt paths; no cwd is changed
            # during fitting or prediction, and it is restored immediately.
            with _working_directory(self.frozen_root):
                names, holdouts = self._psource.fixed_names_and_countries()
            self.taxa = tuple(names)
            if len(self.taxa) != 106 or not set(COUNTRIES).issubset(holdouts):
                raise RuntimeError("ORIGINAL_CR_PA_106_SCOPE_CHANGED")
            header = _read(d / "gbif_archive_header_preflight.json")
            accepted = self._names.name_map(
                _read(d / "gbif_search_preflight.json"),
                _read(d / "plant_search_preflight.json"),
            )["plant"]
            cells = self._source.strict_cell_records(
                self.archive_path, group="plant", source=header["files"]["plant"],
                accepted=accepted, expected_count=367988,
            )
            self._source.validate_against_full_qc(
                "plant", cells, _read(d / "gbif_full_source_qc.json"),
            )
            countries = _read(d / "NEOBAT_FULL_SITE_REFERENCE_EMBARGO_FROZEN_20261119.json")["GBIF_29_country_universe"]
            old = _read(d / "plant_106x17_source_effort_transfer.json")
            original_counts = {(r["plant"], r["holdout_country"]): r
                               for r in old["plant_country_source_rank_results"]}
            if len(countries) != 29 or len(original_counts) != 1802:
                raise RuntimeError("ORIGINAL_PLANT_COUNTRY_DENOMINATOR_CHANGED")
            if old["status"] != "EXPLORATORY_ORIGINAL_106x17_PLANT_SOURCE_EFFORT_TRANSFER_COMPLETE":
                raise RuntimeError("ORIGINAL_PLANT_TRAINING_RECEIPT_STATUS_CHANGED")
            self.raster_dir.mkdir(parents=True, exist_ok=True)
            members, raster_metadata = self._plant.verify_raster_sources(self.raster_dir)
            self._rasters = self._plant.open_source_rasters(self._stack, members)
            (self._source_rows, self._country_cells,
             self._transformer, self._environment) = self._shadow.prepare_source_plant_rows(
                cells, self.taxa, countries, self._rasters,
            )
            # Fit all 212 original specifications before external plot scores.
            for country in COUNTRIES:
                for taxon in self.taxa:
                    previous = original_counts[taxon, country]
                    rows, npos, nbg = self._shadow.plant_fit_rows(
                        taxon, country, self._source_rows, self._country_cells, None, previous,
                    )
                    identified = _training_rows_with_cells(
                        self._source_rows, self._country_cells, country, taxon,
                    )
                    if [(label, env) for _, label, env in identified] != rows:
                        raise RuntimeError("TRAINING_CELL_MEMBERSHIP_DOES_NOT_REPLAY_FROZEN_ROWS")
                    self._models[country, taxon] = self._shadow.train_source_plant_model(rows)
                    self._fit_records.append({
                        "country": country, "taxon": taxon,
                        "train_positive_rows": npos, "train_background_rows": nbg,
                        "expected_train_positive_rows": previous["train_source_matched_focal_cells"],
                        "expected_train_background_rows": previous["train_source_matched_target_background_cells"],
                        "unique_training_cells": len({cell for cell, _, _ in identified}),
                        "original_training_counts_match": True,
                        "training_cell_membership_matches_original_fit_rows": True,
                    })
            packages = {name: importlib.metadata.version(name)
                        for name in (*ORIGINAL_PACKAGES, "scipy")}
            self._metadata = {
                "model_family": "fixed106_country_excluded_climate_only_weak_shadow_plant_component",
                "frozen_code_commit": FROZEN_COMMIT,
                "code_sources": code_sources,
                "plant_GBIF_DOI": "10.15468/dl.xwc5zf",
                "plant_archive_sha256": archive_sha,
                "fixed106_taxa_sha256": FIXED106_SHA256,
                "countries": list(COUNTRIES), "plant_taxon_count": 106,
                "expected_fit_count": 212, "completed_fit_count": len(self._models),
                "features": ["BIO1", "BIO12", "ELEV"],
                "grid": "EPSG:6933_25000m_cell_centroid",
                "raster_sources": raster_metadata,
                "model": {"class": "sklearn.linear_model.LogisticRegression",
                          "C": 1.0, "class_weight": "balanced", "max_iter": 400,
                          "solver": "lbfgs", "random_state": 20261119},
                "transform": "StandardScaler_fit_on_original_outcountry_training_only",
                "minimum_original_training_positive_rows": 20,
                "minimum_original_training_background_rows": 20,
                "python_version": sys.version.split()[0],
                "package_versions": packages,
                "original_pinned_package_versions": dict(ORIGINAL_PACKAGES),
                "pinned_package_versions_match": all(packages[k] == v for k, v in ORIGINAL_PACKAGES.items()),
                "BIEN_data_used_for_training": False,
                "bat_outcome_data_opened": False,
                "independent_source_validation_established": False,
                "ecological_M3_estimated": False,
                "relative_scores_are_calibrated_occupancy": False,
                "training_cell_semantics": "exact union of cell identifiers represented by the original fit rows; duplicate source-country rows retained in fit counts",
                "raw_coordinates_or_cells_in_provenance": False,
            }
            self._entered = True
            return self
        except BaseException:
            self.close()
            raise

    def _require_country(self, country):
        if not self._entered:
            raise RuntimeError("FROZEN_PLANT_COMPONENT_CONTEXT_NOT_OPEN")
        if country not in COUNTRIES:
            raise ValueError("ONLY_FIXED_CR_AND_PA_EXTERNAL_DIAGNOSTIC_ALLOWED")

    def training_cells(self, country, taxon):
        """Exact original training-cell union, in memory; do not serialize."""
        self._require_country(country)
        if taxon not in self.taxa:
            raise ValueError("TAXON_OUTSIDE_FIXED_106")
        return frozenset(cell for cell, _, _ in _training_rows_with_cells(
            self._source_rows, self._country_cells, country, taxon,
        ))

    def predict(self, country, cell_ids):
        """Return (relative-score mapping, raster-invalid cells), without filtering labels.

        The caller must remove evaluation cells overlapping training_cells.
        This method does not infer absences, select taxa, or calculate metrics.
        """
        self._require_country(country)
        import numpy as np
        from scipy.special import expit
        cells = set()
        for value in cell_ids:
            if not isinstance(value, (tuple, list)) or len(value) != 2 or any(
                isinstance(i, bool) or not isinstance(i, numbers.Integral) for i in value
            ):
                raise ValueError("CELL_ID_MUST_BE_TWO_EPSG6933_GRID_INTEGERS")
            cells.add((int(value[0]), int(value[1])))
        valid = {}
        invalid = set()
        for cell in sorted(cells):
            env = self._plant.extract_environment(
                cell, self._rasters, self._transformer, self._environment,
            )
            if env is None:
                invalid.add(cell)
            else:
                valid[cell] = env
        if not valid:
            return {}, frozenset(invalid)
        ordered = list(valid)
        x = np.asarray([valid[cell] for cell in ordered], dtype=float)
        result = {cell: {} for cell in ordered}
        for taxon in self.taxa:
            scaler, model = self._models[country, taxon]
            scores = expit(model.decision_function(scaler.transform(x)))
            if not np.all(np.isfinite(scores)) or np.any(scores < 0) or np.any(scores > 1):
                raise RuntimeError("FROZEN_PLANT_PREDICTION_INVALID")
            for cell, score in zip(ordered, scores):
                result[cell][taxon] = float(score)
        return result, frozenset(invalid)

    def provenance(self):
        """JSON-safe aggregate fit provenance, including all 212 training counts."""
        return copy.deepcopy({**self._metadata, "training_fits": self._fit_records})

    def close(self):
        if self._stack is not None:
            self._stack.close()
            self._stack = None
        self._models.clear()
        self._source_rows.clear()
        self._country_cells.clear()
        self._environment.clear()
        self._entered = False

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
