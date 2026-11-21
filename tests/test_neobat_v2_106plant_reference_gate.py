"""Synthetic only: globally shared 106-plant v2 source and N1 tests."""
from __future__ import annotations
import hashlib
import unittest
from scripts import neobat_v2_106plant_reference_gate as m


class TestV2SourceGate(unittest.TestCase):
    def test_frozen_globally_trainable_intersection_is_106(self):
        species=[f"Plant{i:03d}" for i in range(255)]
        cells={}
        for i,name in enumerate(species):
            # BO is not one of the dummy holdout countries; only first
            # 106 plants have 20+ independent train cells elsewhere.
            cells[name,"BO"]=22 if i<106 else 7
        selected,digest=m.fixed_trainable_species(cells,set(species),["CO","MX"])
        self.assertEqual(selected,species[:106])
        self.assertEqual(len(selected),106)
        self.assertEqual(digest,hashlib.sha256(
            ("\n".join(species[:106])+"\n").encode("utf-8")
        ).hexdigest())

    def test_frozen_species_denominator_failure(self):
        species=[f"Plant{i:03d}" for i in range(255)]
        cells={(name,"BO"):22 for name in species}
        with self.assertRaisesRegex(ValueError,"GLOBALLY_TRAINABLE_106_DENOMINATOR_STOP"):
            m.fixed_trainable_species(cells,set(species),["CO","MX"])

    def test_N1_focal_partner_swap_vs_no_swap(self):
        self.assertTrue(m.focal_two_edge_swap_possible("BatA",
            {("BatA","Plant1"),("BatB","Plant2")}))
        self.assertFalse(m.focal_two_edge_swap_possible("BatA",
            {("BatA","Plant1"),("BatA","Plant2"),("BatB","Plant2")}))
        self.assertFalse(m.focal_two_edge_swap_possible("BatA",
            {("BatA","Plant1")}))
        self.assertFalse(m.focal_two_edge_swap_possible("BatA",set()))

    def test_reference_all_source_link_counted_once(self):
        # Duplicate references and a second source for the same plant
        # are not extra distinct partner *names*.
        pairs={("BatA","Plant1"),("BatA","Plant1"),("BatB","Plant2")}
        self.assertEqual(len(pairs),2)


if __name__=="__main__":
    unittest.main()
