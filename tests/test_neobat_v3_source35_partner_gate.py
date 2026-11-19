"""Source-free provenance and algorithm checks for fixed global source35 plant gate."""
from __future__ import annotations

import copy
import hashlib
import unittest

from scripts import neobat_v3_source35_partner_gate as m
from scripts.neobat_v2_106plant_reference_gate import focal_two_edge_swap_possible


class TestFixedSourceDisjoint35(unittest.TestCase):
    def inputs(self):
        return (m.read(m.D/"v2_106plant_reference_input_gate.json"),
                m.read(m.D/"plant_106x17_global_source_embargo.json"),
                m.read(m.D/"NEOBAT_STRICT_84_COUNTRY_FOLD_ROSTER_FROZEN_20261119.json"))

    def test_original_full_source_support_yields_35_fixed_plants(self):
        v2,source,roster=self.inputs()
        selected,sha,countries=m.fixed_source35(v2,source,roster)
        self.assertEqual(len(selected),35)
        self.assertEqual(len(set(selected)),35)
        self.assertEqual(selected,sorted(selected))
        self.assertEqual(len(countries),17)
        self.assertEqual(sha,hashlib.sha256(
            ("\n".join(selected)+"\n").encode()).hexdigest())
        self.assertEqual(len(source["plant_country_input_gates"]),1802)

    def test_one_source_cell_threshold_drift_cannot_silently_reselect(self):
        v2,source,roster=self.inputs()
        selected,_,countries=m.fixed_source35(v2,source,roster)
        mutated=copy.deepcopy(source)
        target=next(x for x in mutated["plant_country_input_gates"]
                    if x["plant"]==selected[0] and x["holdout_country"]==countries[0])
        target["train_focal_recorded_cells_disjoint_datasets"]=19
        with self.assertRaisesRegex(RuntimeError,"GLOBAL_SOURCE35_INTERSECTION_COUNT_CHANGED"):
            m.fixed_source35(v2,mutated,roster)

    def test_never_expand_species_roster_after_original_fail(self):
        v2,source,roster=self.inputs()
        bad=copy.deepcopy(roster)
        bad["strict_84_candidate_folds"].pop()
        with self.assertRaisesRegex(RuntimeError,"FROZEN_84"):
            m.fixed_source35(v2,source,bad)

    def test_focal_bipartite_two_edge_swap_true_and_false(self):
        self.assertTrue(focal_two_edge_swap_possible(
            "Bat1",{("Bat1","Plant1"),("Bat2","Plant2")}))
        self.assertFalse(focal_two_edge_swap_possible(
            "Bat1",{("Bat1","Plant1"),("Bat1","Plant2"),("Bat2","Plant2")}))
        self.assertFalse(focal_two_edge_swap_possible(
            "Bat1",{("Bat2","Plant2")}))

    def test_source_gate_output_cannot_be_called_an_ecological_fit(self):
        self.assertEqual(m.SUCCESS,
            "EXPLORATORY_V3_SOURCE_DISJOINT_35PLANT_FRUIT_PARTNER_GATE")
        self.assertEqual(m.N_PAIRS,84)


if __name__=="__main__":
    unittest.main()
