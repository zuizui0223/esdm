"""Check the location embargo independently of fitting and external services."""
import importlib.util
import pathlib
import subprocess
import sys
import unittest

import pytest

from scripts import neobat_bien_frozen_plant_adapter as adapter


ADAPTER = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "neobat_bien_frozen_plant_adapter.py"


def test_default_scope_remains_cr_pa_and_requested_scope_is_preserved(tmp_path):
    default = adapter.FixedPlantComponent(tmp_path, tmp_path / "plants.zip", tmp_path)
    assert default.countries == ("CR", "PA")
    expanded = adapter.FixedPlantComponent(
        tmp_path, tmp_path / "plants.zip", tmp_path,
        countries=("BR", "EC", "GF", "GT", "HN", "NI", "PE", "SV"),
    )
    assert expanded.countries == ("BR", "EC", "GF", "GT", "HN", "NI", "PE", "SV")
    # Country validation must not require opening archives or model libraries.
    assert not (tmp_path / "plants.zip").exists()


@pytest.mark.parametrize("countries", [("MX",), ("BR", "CR", "MX"), (),
                                       ("BR", "BR"), ("br",), "BR"])
def test_invalid_country_request_is_rejected_before_original_inputs_open(tmp_path, countries):
    with pytest.raises(ValueError, match="COUNTR"):
        adapter.FixedPlantComponent(tmp_path, tmp_path / "missing.zip", tmp_path,
                                    countries=countries)


def test_each_requested_country_requires_one_original_receipt_for_every_taxon():
    taxa = tuple(f"Plant {i}" for i in range(106))
    rows = [{"holdout_country": country, "plant": taxon}
            for country in ("BR", "GF") for taxon in taxa]
    counts = adapter._requested_original_counts(rows, taxa, ("BR", "GF"))
    assert len(counts) == 212
    # Having 106 rows is insufficient if one plant is duplicated and another lost.
    duplicated = [*rows[:-1], rows[-2]]
    with pytest.raises(RuntimeError, match="ORIGINAL_REQUESTED_PLANT_COUNTRY_RECEIPT"):
        adapter._requested_original_counts(duplicated, taxa, ("BR", "GF"))
    with pytest.raises(RuntimeError, match="ORIGINAL_REQUESTED_PLANT_COUNTRY_RECEIPT"):
        adapter._requested_original_counts(rows[:-1], taxa, ("BR", "GF"))
    with pytest.raises(RuntimeError, match="ORIGINAL_REQUESTED_PLANT_COUNTRY_RECEIPT"):
        adapter._requested_original_counts(rows, taxa, ("BR", "PE"))


class TrainingCellSelectionTest(unittest.TestCase):
    def test_holdout_and_border_cells_never_enter_training_set(self):
        self.assertTrue(ADAPTER.exists(), "the frozen plant adapter is not implemented")
        spec = importlib.util.spec_from_file_location("frozen_adapter_test", ADAPTER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source = {
            "tree": {
                "CR": [((1, 1), 1, (10.0, 20.0, 30.0))],
                "PA": [
                    ((2, 2), 1, (10.0, 20.0, 30.0)),
                    ((3, 3), 0, (11.0, 21.0, 31.0)),
                    ((9, 9), 1, (12.0, 22.0, 32.0)),
                ],
                "MX": [((2, 2), 1, (10.0, 20.0, 30.0))],
            }
        }
        # (9, 9) was recorded for another taxon in the held-out country.
        # It must be excluded even though tree's CR source rows omit it.
        country_cells = {"CR": {(1, 1), (9, 9)}}
        rows = module._training_rows_with_cells(source, country_cells, "CR", "tree")
        self.assertEqual([r[0] for r in rows], [(2, 2), (3, 3), (2, 2)])
        self.assertEqual(frozenset(r[0] for r in rows), {(2, 2), (3, 3)})
        # Preserve repeated source-country observations in fit row counts.
        self.assertEqual(sum(r[1] for r in rows), 2)

    def test_import_does_not_load_model_libraries_or_original_scripts(self):
        self.assertTrue(ADAPTER.exists(), "the frozen plant adapter is not implemented")
        code = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location('adapter', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert not any(name in sys.modules for name in ('numpy','sklearn','rasterio','pyproj'))
assert not any(name.startswith('scripts.neobat_') for name in sys.modules)
"""
        subprocess.run([sys.executable, "-c", code, str(ADAPTER)], check=True)


if __name__ == "__main__":
    unittest.main()
