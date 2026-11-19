"""Synthetic regression for prospectively frozen NeoBat 25km colocation audit."""
from __future__ import annotations

import unittest
from collections import defaultdict
from copy import deepcopy
from scripts import neobat_same_cell_source_support as m

BAT="Testus bat"
PLANTS=("Plant a","Plant b","Plant c","Plant d","Plant e")


def trial():
    # Cell IDs are synthetic and are never interpreted as GPS coordinates.
    cells={
      "bat":{
        (BAT,"CO"):{(0,0):{"S1"},(1,0):{"S1"},(2,0):{"S1"},
                    (3,0):{"S1"},(4,0):{"S1"}},
        (BAT,"MX"):{(x,2):{"S1"} for x in range(20)}
      },
      "plant":{}
    }
    for i,plant in enumerate(PLANTS):
        cells["plant"][(plant,"CO")]={
           (x,0):{"S1" if i==0 else "P1"} for x in range(5)
        }
        # independent outcountry support for ALL 5 test plants
        cells["plant"][(plant,"MX")]={
            (x,3):{"P2"} for x in range(20)
        }
    # Partner plants a/b/c; source country MX distinct from CO and 2 refs
    links=[
      (BAT,PLANTS[0],"R1","MX"),
      (BAT,PLANTS[1],"R1","MX"),
      (BAT,PLANTS[2],"R2","MX"),
    ]
    return cells,links


class TestSameCellSourceSupport(unittest.TestCase):
    def test_same_cell_counts_and_distinct_dataset(self):
        cells,links=trial()
        count,total=m.support_counts(cells)
        row=m.one_fold(BAT,"CO",cells,links,count,total,list(PLANTS),{"CO":[]})
        self.assertEqual(row["known_precision_bat_recorded_cells"],5)
        self.assertEqual(row["qualified_partner_species"],3)
        self.assertEqual(row["qualified_generic_plant_species"],5)
        self.assertEqual(row["qualified_nonpartner_species"],2)
        self.assertEqual(row["training_original_NeoBat_refs"],2)
        self.assertEqual(row["bat_cells_with_at_least_one_linked_plant_record"],5)
        self.assertEqual(row["bat_cells_with_at_least_three_linked_plant_species"],5)
        self.assertEqual(row["bat_cells_with_any_generic_plant_record"],5)
        self.assertEqual(row["bat_cells_with_any_nonpartner_plant_record"],5)
        self.assertEqual(row["bat_cells_with_linked_plant_from_distinct_GBIF_dataset"],5)
        self.assertTrue(row["zero_does_not_mean_partner_absence"])

    def test_no_source_confusion_and_zero_not_absence(self):
        cells,links=trial()
        for plant in PLANTS[:3]:
            # Shift partners to nonoverlapping cells but retain country
            # and outside-country input eligibility.
            cells["plant"][(plant,"CO")]={(x+10,0):{"P1"} for x in range(5)}
        count,total=m.support_counts(cells)
        row=m.one_fold(BAT,"CO",cells,links,count,total,list(PLANTS),{"CO":[]})
        self.assertEqual(row["bat_cells_with_at_least_one_linked_plant_record"],0)
        self.assertEqual(row["bat_cells_with_any_nonpartner_plant_record"],5)
        self.assertTrue(row["zero_does_not_mean_partner_absence"])

    def test_paper_embargo_is_global_not_only_country_row_filter(self):
        cells,links=trial()
        count,total=m.support_counts(cells)
        # When a ref is present in the holdout country original site table,
        # even the outcountry MX link sharing it must be excluded.
        with self.assertRaisesRegex(RuntimeError,"FROZEN_SOURCE_PARTNER"):
            m.one_fold(BAT,"CO",cells,links,count,total,list(PLANTS),
                       {"CO":["R2"]})

    def test_datasets_same_source_not_independent(self):
        self.assertFalse(m.different_dataset_in_same_cell({"S1"},{"S1"}))
        self.assertFalse(m.different_dataset_in_same_cell({""},{"S2"}))
        self.assertFalse(m.different_dataset_in_same_cell({"S1"},{""}))
        self.assertTrue(m.different_dataset_in_same_cell({"S1"},{"S2"}))
        self.assertTrue(m.different_dataset_in_same_cell({"S1","S2"},{"S1"}))

    def test_strict_count_replay_stops_on_source_drift(self):
        cells,links=trial()
        qc={"status":"BOTH_COMPLETE_GBIF_SOURCE_QC_VERIFIED",
            "groups":{"bat":{
                "DOI":m.EXPECTED["bat"]["doi"],
                "source_archive_sha256":m.EXPECTED["bat"]["archive_sha"],
                "full_archive_rows_checked":m.EXPECTED["bat"]["n_records"],
                "species_country_summary":[{
                    "taxon":BAT,"country":"CO",
                    "precision_le12500m_25km_cells":6}]
            }}}
        with self.assertRaisesRegex(RuntimeError,"COUNTRY_SPECIES_STRICT_CELL_COUNT_DRIFT"):
            m.validate_against_full_qc("bat",cells["bat"],qc)

    def test_frozen_84_roster_fail_closed(self):
        cells,links=trial()
        with self.assertRaisesRegex(RuntimeError,"FROZEN_84_CANDIDATE_ROSTER_MISMATCH"):
            m.roster_matches(cells,links,[BAT],list(PLANTS),["CO","MX"],
                             {"CO":[]},[(BAT,"CO")])


if __name__=="__main__":
    unittest.main()
