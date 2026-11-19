"""Synthetic only: M0/M1/M2/M3/N1 rank, links and leakage/firewall tests."""
from __future__ import annotations
import importlib.util
import unittest
from copy import deepcopy
from scripts import neobat_model_comparison_core as m

HAS_NUMPY=importlib.util.find_spec("numpy") is not None

PLANTS=("Ficus insipida","Piper aduncum","Cecropia obtusifolia",
        "Ficus trigonata","Solanum rugosum","Cecropia obtusa")
BAT="Testus frugivorus"
OTHER="Testus omnivorus"

def toy():
    manifest={"synthetic":True,
              "site_reference_embargo_by_holdout":{"BR":[]},
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
           # Each presence and paired target background has identical
           # environment/effort. M0 cannot discriminate on known truth.
           "temperature":10+(i//2)*0.1,"precipitation":50+((i//2)%3),
           "forest":0.4+((i//2)%4)/10,"topography":(i//2)%3,
           "effort":0.5+((i//2)%2)*0.1}
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
        self.assertIn("M2",result["presence_rank_auc"])
        self.assertIn("M3",result["presence_rank_auc"])
        self.assertTrue(all(0<=v<=1 for v in result["presence_rank_auc"].values()))
        # Known-truth gate: generic B is deliberately uninformative;
        # only the actual outcountry documented fruit partners add signal.
        self.assertAlmostEqual(result["presence_rank_auc"]["M0"],0.5,places=6)
        self.assertAlmostEqual(result["presence_rank_auc"]["M1"],0.5,places=6)
        self.assertGreaterEqual(result["presence_rank_auc"]["M2"],0.95)
        self.assertGreaterEqual(result["presence_rank_auc"]["M3"],0.95)
        self.assertGreater(result["secondary_M2_minus_M0"],0.4)
        self.assertAlmostEqual(result["secondary_M3_minus_M2"],0.0,places=6)
        self.assertGreaterEqual(result["N1_distinct_focal_partner_sets"],2)
        self.assertLessEqual(result["N1_draws_with_unchanged_focal_partners"],9)
        self.assertGreater(result["heldout_M3_minus_M1"],0.4)
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
        filtered,banned=m._training_links(links,"BR",set(PLANTS),["R0"])
        self.assertIn("R0",banned)
        self.assertNotIn("R0",{x["ref_id"] for x in filtered})

    def test_holdout_entire_site_reference_embargo_is_required(self):
        rows,plants,links,manifest=toy()
        # A source reference from heldout BR may be absent from the fruit
        # link table but present in the COMPLETE NeoBat Sites table.
        links.append({"bat":BAT,"plant":PLANTS[0],
                      "ref_id":"SHARED_HIDDEN_SITE","source_country":"MX"})
        manifest["site_reference_embargo_by_holdout"]["BR"]=["SHARED_HIDDEN_SITE"]
        filtered,banned=m._training_links(links,"BR",set(PLANTS),
                                            manifest["site_reference_embargo_by_holdout"]["BR"])
        self.assertIn("SHARED_HIDDEN_SITE",banned)
        self.assertNotIn("SHARED_HIDDEN_SITE",{r["ref_id"] for r in filtered})
        with self.assertRaisesRegex(m.QualificationStop,"NO_ORIGINAL_SITE_REFERENCE_EMBARGO"):
            bad=deepcopy(manifest)
            bad.pop("site_reference_embargo_by_holdout")
            m.compare_fold(rows,plants,links,bad,BAT,"BR",null_draws=1)
        missing=[{"bat":OTHER,"plant":PLANTS[4],
                  "ref_id":"VISIBLE_BR","source_country":"BR"}]+links
        with self.assertRaisesRegex(m.QualificationStop,"INCOMPLETE_SITE_REFERENCE_EMBARGO"):
            m._training_links(missing,"BR",set(PLANTS),["SHARED_HIDDEN_SITE"])

    def test_real_model_requires_citable_255_rasters(self):
        rows,plants,links,manifest=toy()
        manifest["synthetic"]=False
        with self.assertRaisesRegex(m.QualificationStop,"MISSING_OR_CHANGED_GBIF_DOI"):
            m.compare_fold(rows,plants,links,manifest,BAT,"BR",null_draws=1)

    @unittest.skipUnless(HAS_NUMPY,"numpy only for model fit")
    def test_null_must_change_focal_partners_not_merely_other_bats(self):
        rows,plants,links,manifest=toy()
        links=[{"bat":BAT,"plant":plant,"ref_id":f"R{i}",
                "source_country":"MX"} for i,plant in enumerate(PLANTS)]
        # The focal bat already connects to every plant, so its partner
        # identities cannot vary although nonfocal species can rewire.
        links += [
            {"bat":OTHER,"plant":PLANTS[0],"ref_id":"O0","source_country":"MX"},
            {"bat":OTHER,"plant":PLANTS[3],"ref_id":"O3","source_country":"MX"},
            {"bat":"Testus tertius","plant":PLANTS[1],"ref_id":"T1","source_country":"MX"},
            {"bat":"Testus tertius","plant":PLANTS[4],"ref_id":"T4","source_country":"MX"},
        ]
        self.assertTrue(m._is_rewirable(m._network_edges(links)))
        with self.assertRaisesRegex(m.QualificationStop,
                                    "NULL_FOCAL_LINK_IDENTITIES_INVARIANT"):
            m.compare_fold(rows,plants,links,manifest,BAT,"BR",null_draws=9)

    @unittest.skipUnless(HAS_NUMPY,"numpy only for model fit")
    def test_known_truth_partner_identity_beats_rewired_null_when_identifiable(self):
        """A distinct, intentionally noisy synthetic case, not biological evidence.

        The three true plants carry a shared source-known signal. Nine
        independent nonpartners have spatially varying but irrelevant scores.
        Rewiring across four degree-matched bat species should degrade
        heldout prediction; a toy with complementary plants could not
        prove that the implementation distinguishes true partners from N1.
        """
        import numpy as np
        universe=tuple(f"Testplant{i:02d}" for i in range(12))
        rng=np.random.default_rng(20261119)
        manifest={"synthetic":True,
                  "site_reference_embargo_by_holdout":{"BR":[]},
                  "outer_holdout_regions":["BR"],
                  "plant_universe":list(universe)}
        rows=[]
        preds=[]
        for i in range(240):
            heldout=i>=160
            case=(i%2==0)
            sign=1 if case else -1
            cell=f"noise_cell_{i}"
            pair=i//2
            rows.append({
                "bat":BAT,"region":"BR" if heldout else "MX",
                "cell_id":cell,"source_event_id":f"noise_event_{i}",
                "source_dataset_key":f"noise_dataset_{i//12}",
                "role":"presence" if case else "target_background",
                # Observational covariates are matched within each
                # presence/background pair; they cannot encode the label.
                "temperature":15+(pair%5),
                "precipitation":60+(pair%7),
                "forest":0.3+(pair%4)*0.1,
                "topography":pair%3,
                "effort":0.3+(pair%4)*0.1
            })
            vals=np.clip(np.concatenate([
                0.5+0.17*sign+rng.normal(0,0.13,3),
                0.5+rng.normal(0,0.22,9)]),0.01,0.99)
            for j,plant in enumerate(universe):
                preds.append({"holdout_region":"BR","cell_id":cell,
                              "plant":plant,
                              "relative_suitability":float(vals[j]),
                              "excluded_from_plant_training":True})
        links=[]
        for k in range(4):
            bat=BAT if k==0 else f"Testus nonfocal{k}"
            for j in range(3):
                links.append({"bat":bat,"plant":universe[k*3+j],
                              "ref_id":f"noise_ref_{k}_{j}",
                              "source_country":"MX"})
        result=m.compare_fold(rows,preds,links,manifest,BAT,"BR",
                              null_draws=39,seed=20261119)
        self.assertGreater(result["presence_rank_auc"]["M3"],0.95)
        self.assertGreater(result["heldout_M3_minus_M1"],0.10)
        self.assertGreater(result["M3_minus_rewired_N1_mean"],0.08)
        self.assertGreater(result["N1_distinct_focal_partner_sets"],10)
        self.assertFalse(result["causal_interaction_established"])

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
