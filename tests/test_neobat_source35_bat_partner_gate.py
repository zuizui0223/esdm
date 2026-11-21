"""Source-free synthetic global 35 plant derivation and original-84 stops."""
from __future__ import annotations
import hashlib
import unittest

from scripts import neobat_source35_bat_partner_gate as m


def example():
    plants=[f"Plant{i:03d}" for i in range(106)]
    countries=["CO"]+[f"C{i:02d}" for i in range(16)]
    rows=[]
    for p in plants:
        for c in countries:
            admissible=(int(p[-3:])<35 or c!="CO")
            rows.append({
                "plant":p,"holdout_country":c,
                "train_quantity_eligible_after_global_dataset_embargo":admissible
            })
    gate={"status":m.SOURCE_STATUS,
          "summary":{
              "original_1802_denominator_intact":True,
              "source_disjoint_trainable_plant_species_all_17_holdouts":35
          },
          "plant_country_input_gates":rows}
    return plants,countries,gate


class TestSource35(unittest.TestCase):
    def test_fixed35_name_selection_independent_of_bat_diet(self):
        plants,countries,source=example()
        selected,digest=m.global_disjoint_names(source,plants,countries)
        self.assertEqual(selected,plants[:35])
        self.assertEqual(digest,hashlib.sha256(
            ("\n".join(plants[:35])+"\n").encode()).hexdigest())

    def test_duplicate_original_1802_source_pair_stops(self):
        plants,countries,source=example()
        source["plant_country_input_gates"][1]=source["plant_country_input_gates"][0]
        with self.assertRaisesRegex(ValueError,"DUPLICATE_1802"):
            m.global_disjoint_names(source,plants,countries)

    def test_declared_35_denominator_not_relaxed(self):
        plants,countries,source=example()
        source["plant_country_input_gates"][35*17][
            "train_quantity_eligible_after_global_dataset_embargo"]=True
        with self.assertRaisesRegex(ValueError,"SOURCE_DISJOINT_35_GLOBAL_PLANT_NUMBER_DRIFT"):
            m.global_disjoint_names(source,plants,countries)

    def test_original_source_eligibility_required(self):
        plants,countries,source=example()
        source["status"]="SOURCE_FAILURE"
        with self.assertRaisesRegex(ValueError,"ORIGINAL_1802_DISJOINT_SOURCE_GATE"):
            m.global_disjoint_names(source,plants,countries)


if __name__=="__main__":
    unittest.main()
