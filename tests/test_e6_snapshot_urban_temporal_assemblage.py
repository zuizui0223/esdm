"""Unit tests for frozen SNAPSHOT USA temporal assembly: all values synthetic."""
from __future__ import annotations

import csv
from datetime import datetime
import hashlib
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from scripts import e6_snapshot_urban_temporal_assemblage as e6


class E6SnapshotTest(unittest.TestCase):
    def test_deep_night_and_midday_are_fixed_not_response_selected(self):
        self.assertEqual(e6.recorded_clock_bin(datetime(2024,9,15,2)), "night")
        self.assertEqual(e6.recorded_clock_bin(datetime(2024,9,15,21)), "night")
        self.assertEqual(e6.recorded_clock_bin(datetime(2024,9,15,10)), "midday")
        self.assertEqual(e6.recorded_clock_bin(datetime(2024,9,15,15)), "midday")
        for hour in (4,5,6,7,8,9,16,17,18,19,20):
            self.assertIsNone(e6.recorded_clock_bin(datetime(2024,9,15,hour)))

    def test_binomial_wildlife_eligibility_excludes_humans_and_pets(self):
        self.assertEqual(e6.scientific_name("Procyon", "lotor"), "Procyon lotor")
        self.assertIsNone(e6.scientific_name("Felis", "catus"))
        self.assertIsNone(e6.scientific_name("Homo", "sapiens"))
        self.assertIsNone(e6.scientific_name("Canis", "sp."))
        self.assertIsNone(e6.scientific_name("", "latrans"))
        self.assertEqual(e6.TOP_N, 12)

    def test_predeclared_panel_uses_only_historical_presence_support(self):
        occupancy={
            "Canis latrans": {("a",2020),("b",2020)},
            "Procyon lotor": {("a",2020),("b",2020)},
            "Odocoileus virginianus": {("a",2020)},
        }
        sites={"Canis latrans":4,"Procyon lotor":5,"Odocoileus virginianus":15}
        self.assertEqual(e6.fixed_top_taxa(occupancy,sites)[:2],
                         ["Procyon lotor","Canis latrans"])

    def test_exact_mh_and_array_leave_one_out(self):
        arrays = {f"array{i}":[2.0,8.0,3] for i in range(6)}
        q=e6.calculate_group(arrays)
        self.assertEqual(q["arrays"],6)
        self.assertEqual(q["informative_site_years"],18)
        self.assertAlmostEqual(q["odds"],0.25)
        self.assertTrue(q["full_loo"])
        self.assertAlmostEqual(q["loo_min"],0.25)
        self.assertAlmostEqual(q["loo_max"],0.25)

    def test_nonidentifiable_zero_crossproduct_stays_missing(self):
        arrays={f"array{i}":[0.0,10.0,3] for i in range(6)}
        q=e6.calculate_group(arrays)
        self.assertEqual(q["status"],"ZERO_MH_CROSSPRODUCT")
        self.assertIsNone(q["odds"])

    def test_primary_pair_does_not_assume_same_camera_detection(self):
        self.assertEqual(e6.MIN_ARRAYS,5)
        self.assertEqual(e6.MIN_SITE_YEARS,10)
        self.assertEqual(e6.MIN_CELLS,12)
        self.assertEqual(e6.MIN_SHARED_GRID_CELLS,2)

    @staticmethod
    def _fixture(folder:Path,year:int,prefix:str):
        dep=folder/f"{prefix}_deployments.csv"
        seq=folder/f"{prefix}_sequences.csv"
        dh=["Year","Camera_Trap_Array","Site_Name","Deployment_ID",
            "Development_Level","Latitude","Longitude","Start_Date","End_Date"]
        sh=["Deployment_ID","Sequence_ID","Start_Time","Class","Genus","Species"]
        with dep.open("w",encoding="utf-8",newline="") as d,seq.open("w",encoding="utf-8",newline="") as s:
            dw=csv.DictWriter(d,fieldnames=dh);dw.writeheader()
            sw=csv.DictWriter(s,fieldnames=sh);sw.writeheader()
            for group in ("low","high"):
                for i in range(6):
                    arr=f"{group}-{i}"
                    level=("Wild" if i%2==0 else "Rural") if group=="low" else ("Urban" if i%2==0 else "Suburban")
                    for j in range(3):
                        site=f"site-{j}"
                        depid=f"{year}-{arr}-{j}"
                        dw.writerow({"Year":year,"Camera_Trap_Array":arr,"Site_Name":site,
                                    "Deployment_ID":depid,"Development_Level":level,
                                    "Latitude":37+j*0.01 if i<3 else 42+j*0.01,
                                    "Longitude":-90+j*0.01 if i<3 else -80+j*0.01,
                                    "Start_Date":f"{year}-09-01","End_Date":f"{year}-10-30"})
                        counts=(("Canis","latrans",2,4),("Procyon","lotor",4,2)) if group=="low" else (
                            ("Canis","latrans",4,2),("Procyon","lotor",2,4))
                        n=0
                        for genus,species,night,day in counts:
                            for hour, count in ((23,night),(12,day)):
                                for k in range(count):
                                    n+=1
                                    sw.writerow({"Deployment_ID":depid,"Sequence_ID":f"q{n}",
                                                "Start_Time":f"{year}-09-15 {hour:02d}:00:00",
                                                "Class":"Mammalia","Genus":genus,"Species":species})
                        if year==2024:
                            n+=1
                            sw.writerow({"Deployment_ID":depid,"Sequence_ID":f"q{n}",
                                        "Start_Time":f"{year}-09-15 23:00:00",
                                        "Class":"Mammalia","Genus":"Ursus","Species":"americanus"})
        return dep,seq

    def test_full_train_plus_heldout_is_repeatable_and_not_source_mixed(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            hd,hs=self._fixture(root,2020,"history")
            vd,vs=self._fixture(root,2024,"2024")
            def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
            with (patch.dict(e6.DATA["history"],
                             {"deployment_sha256":sha(hd),"sequence_sha256":sha(hs)}),
                  patch.dict(e6.DATA["holdout_2024"],
                             {"deployment_sha256":sha(vd),"sequence_sha256":sha(vs)})):
                r=e6.audit(hd,hs,vd,vs)
            self.assertEqual(r["historical_taxon_panel_selected_before_2024_response"],
                             ["Canis latrans","Procyon lotor"])
            self.assertEqual(r["historical"]["fixed_species_pair_count"],1)
            self.assertEqual(r["holdout_2024"]["fixed_species_pair_count"],1)
            for cohort in ("historical","holdout_2024"):
                self.assertEqual(r[cohort]["national_comparable"],1)
                self.assertEqual(r[cohort]["shared_development_grid_cells"],2)
                self.assertEqual(r[cohort]["national_rank_reversals"],1)
                self.assertEqual(r[cohort]["national_array_deletion_robust_directions"],1)
                pair=r[cohort]["all_pairs"][0]["national"]
                self.assertAlmostEqual(pair["groups"]["low"]["odds"],0.25)
                self.assertAlmostEqual(pair["groups"]["high"]["odds"],4)
                self.assertAlmostEqual(pair["development_ratio"],16)
                self.assertEqual(r[cohort]["geographic_sensitivity_comparable"],1)
            self.assertEqual(r["temporal_replication"]["both_years_comparable_pairs"],1)
            self.assertEqual(r["temporal_replication"]["pair_direction_concordance_count"],1)
            self.assertEqual(r["temporal_replication"]["fully_array_deletion_robust_concordant_pairs"],1)
            self.assertFalse(r["claims_boundary"]["animal_activity_separated_from_camera_detection"])
            self.assertFalse(r["claims_boundary"]["E5_original_G4_passed"])


if __name__=="__main__":
    unittest.main()
