"""Synthetic only: M0/M1/M3/N1 rank, outcountry links and firewall tests."""
from __future__ import annotations
import importlib.util
import unittest
from copy import deepcopy
from scripts import neobat_model_comparison_core as m

HAS_NUMPY=importlib.util.find_spec("numpy") is not None

PLANTS=("Ficus insipida","Piper aduncum","Cecropia obtusifolia",
        "Ficus trigonata","Solanum rugosum")
BAT="Testus frugivorus"
OTHER="Testus omnivorus"

def toy():
    manifest={"synthetic":True,
              "outer_holdout_regions":["BR"],
              "plant_universe":list(PLANTS)}
    rows=[]
    preds=[]
    for i in range(16):
        country="MX" if i<10 else "BR"
        case=(i%2==0)
        cell=f"cell_{i}"
        r={"bat":BAT,"region":country,"cell_id":cell,
           "source_event_id":f"event{i}","source_dataset_key":f"ds{i//3}",
           "role":"presence" if case else "target_background",
           "temperature":i*0.1,"precipitation":50+(i%3),
           "forest":0.4+(i%4)/10,"topography":i%3,
           "effort":0.5+(i%2)*0.1}
        rows.append(r)
        for j,plant in enumerate(PLANTS):
            # The first 3 plant features contain a strong synthetic
            # resource signal not collapsed by the generic B mean.
            score=0.8 if case else 0.2
            if j>=3:score=0.2 if case else 0.8
            score=min(0.99,max(0.01,score+(j%2)*0.02))
            preds.append({"holdout_region":"BR","cell_id":cell,"plant":plant,
                          "relative_suitability":score,
                          "excluded_from_plant_training":True})
    links=[]
    for i,plant in enumerate(PLANTS[:3]):
        links.append({"bat":BAT,"plant":plant,"ref_id":f"R{i}",
                      "source_country":["MX","CR","PA"][i]})
    for i,plant in enumerate(PLANTS[3:]):
        links.append({"bat":OTHER,"plant":plant,"ref_id":f"O{i}",
                      "source_country":"MX"})
    return rows,preds,links,manifest

class TestPredictiveCore(unittest.TestCase):
    def test_auc_tie_and_direction(self):
        self.assertEqual(m.rank_auc([1,0],[1,0]),1.0)
        self.assertEqual(m.rank_auc([1,0],[0,1]),0.0)
        self.assertEqual(m.rank_auc([1,0],[0.5,0.5]),0.5)
        with self.assertRaisesRegex(m.QualificationStop,"AUC_NEEDS"):
            m.rank_auc([1,1],[0.5,0.6])

    @unittest.skipUnless(HAS_NUMPY,"numpy only for model fit")
    def test_fixed_holdout_model_and_rewire(self):
        rows,plants,links,manifest=toy()
        result=m.compare_fold(rows,plants,links,manifest,BAT,"BR",null_draws=9)
        self.assertEqual(result["status"],"SYNTHETIC_ONLY")
        self.assertEqual(result["training_events"],10)
        self.assertEqual(result["heldout_events"],6)
        self.assertEqual(result["rewire_draws"],9)
        self.assertEqual(result["trained_fruit_partner_names"],3)
        self.assertIn("M3",result["presence_rank_auc"])
        self.assertTrue(all(0<=v<=1 for v in result["presence_rank_auc"].values()))
        self.assertTrue(result["background_is_not_true_absence"])
        self.assertFalse(result["causal_interaction_established"])

    def test_response_role_and_source_event_firewall(self):
        rows,plants,links,manifest=toy()
        rows[-1]["source_event_id"]=rows[0]["source_event_id"]
        with self.assertRaisesRegex(m.QualificationStop,"DUPLICATE_SOURCE_EVENT"):
            m.compare_fold(rows,plants,links,manifest,BAT,"BR",null_draws=1)
        rows,plants,links,manifest=toy()
        rows[-1]["role"]="absence"
        with self.assertRaisesRegex(m.QualificationStop,"BACKGROUND_IS_NOT_VERIFIED_ABSENCE"):
            m.compare_fold(rows,plants,links,manifest,BAT,"BR",null_draws=1)

    def test_plant_cross_fit_required(self):
        rows,plants,links,manifest=toy()
        plants[-1]["excluded_from_plant_training"]=False
        with self.assertRaisesRegex(m.QualificationStop,"PLANT_TRAINING_CONTAINS_HELDOUT_REGION"):
            m.compare_fold(rows,plants,links,manifest,BAT,"BR",null_draws=1)
        rows,plants,links,manifest=toy()
        plants.pop()
        with self.assertRaisesRegex(m.QualificationStop,"INCOMPLETE_PLANT_CROSS_FITTED_GRID"):
            m.compare_fold(rows,plants,links,manifest,BAT,"BR",null_draws=1)

    def test_outcountry_publication_reference_exclusion(self):
        rows,plants,links,manifest=toy()
        links.append({"bat":OTHER,"plant":PLANTS[4],"ref_id":"R0","source_country":"BR"})
        filtered,banned=m._training_links(links,"BR",set(PLANTS))
        self.assertIn("R0",banned)
        self.assertNotIn("R0",{x["ref_id"] for x in filtered})

    def test_real_model_requires_citable_255_rasters(self):
        rows,plants,links,manifest=toy()
        manifest["synthetic"]=False
        with self.assertRaisesRegex(m.QualificationStop,"MISSING_OR_CHANGED_GBIF_DOI"):
            m.compare_fold(rows,plants,links,manifest,BAT,"BR",null_draws=1)

    def test_rewire_preserves_both_degree_sequences(self):
        rows,plants,links,manifest=toy()
        edges=m._network_edges(links)
        self.assertTrue(m._is_rewirable(edges))
        rng=__import__("random").Random(20261119)
        swapped,n=m.degree_preserving_rewire(edges,rng,500)
        self.assertGreater(n,0)
        def degree(v,axis):return sorted((x,sum(w[axis]==x for w in v))
            for x in set(w[axis] for w in v))
        self.assertEqual(degree(edges,0),degree(swapped,0))
        self.assertEqual(degree(edges,1),degree(swapped,1))

if __name__=="__main__":
    unittest.main()
