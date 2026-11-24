"""Synthetic only shadow S0/S1/S3/SN1 and source data firewall tests."""
from __future__ import annotations

import unittest
import numpy as np
from scripts import neobat_shadow_source_geography_51fold as m


class TestShadowModel(unittest.TestCase):
    def test_plant_country_training_excludes_heldout_cells_and_replays_counts(self):
        rows={"Plant A":{
            "CO":[((1,1),1,(0.1,0.2,1.))],
            "MX":[((1,1),1,(0.1,0.2,1.))]+[
                ((i,2),i%2,(i*.1,0.2,1.)) for i in range(40)]
        }}
        holdout={"CO":{(1,1)}}
        prev={"train_source_matched_focal_cells":20,
              "train_source_matched_target_background_cells":20}
        train,p,b=m.plant_fit_rows("Plant A","CO",rows,holdout,None,prev)
        self.assertEqual((p,b),(20,20))
        self.assertEqual(len(train),40)
        prev["train_source_matched_focal_cells"]=21
        with self.assertRaisesRegex(RuntimeError,"COUNTS_DRIFT"):
            m.plant_fit_rows("Plant A","CO",rows,holdout,None,prev)

    def test_three_climate_feature_source_plant_classifier(self):
        rows=[]
        for i in range(80):
            label=i%2
            env=float(label)*2.-1.
            rows.append((label,(env,env*2.,env*.5)))
        norm,fit=m.train_source_plant_model(rows)
        self.assertGreater(fit.predict_proba(norm.transform([[1.,2.,.5]]))[0,1],.90)

    def test_full_focal_source_rewire_and_model_stays_source_only(self):
        bat="Testus A"
        other="Testus B"
        country_data={}
        bat_env={}
        allcells=[]
        for country,n in (("CO",16),("MX",48)):
            r={}
            for i in range(n):
                cell=(i,0 if country=="CO" else 2)
                ispos=i%2==0
                r[cell]={bat if ispos else other:{"sourceD"}}
                # Source-only known truth, climate deliberately matched
                # enough to avoid total separation of the baseline.
                bat_env[cell]=(float(i//2),.25,float(i%3))
                allcells.append(cell)
            country_data[country]=r
        selected=[f"Plant{i}" for i in range(6)]
        rng=np.random.default_rng(20261119)
        mat=rng.uniform(.1,.9,(len(allcells),6))
        # Source-pinned actual partners 0-2 have extra label-correlated
        # relative suitability; other plants are the rewiring controls.
        for idx,cell in enumerate(allcells):
            positive=(cell[0]%2)==0
            mat[idx,:3]=.9 if positive else .1
        cell_lookup={c:i for i,c in enumerate(allcells)}
        links=[(bat,f"Plant{i}",f"R{i}","MX") for i in range(3)]
        links += [(other,f"Plant{i}",f"O{i}","MX") for i in range(3,6)]
        result=m.country_shadow(bat,"CO",country_data,["MX","CO"],
            bat_env,mat,cell_lookup,selected,links,{"CO":[],"MX":[]})
        self.assertEqual(result["status"],m.STATUS_OK)
        self.assertEqual(result["SN1_draws"],m.N_NULL)
        self.assertGreater(result["SN1_distinct_focal_partner_sets"],1)
        self.assertTrue(result["no_original_ecological_M3_vs_M1_estimated"])
        self.assertTrue(all(0<=result[k]<=1 for k in (
            "S0_abiotic_rank_auc","S1_generic_plant_rank_auc",
            "S3_published_partner_rank_auc","SN1_mean_rewired_rank_auc"
        )))

    def test_bat_test_background_missing_stops_not_absences(self):
        bat="Testus A"
        country_data={
            "CO":{(i,0):{bat:{"D"}} for i in range(10)},
            "MX":{(i,2):{bat if i%2==0 else "Testus B":{"D"}}
                  for i in range(60)}
        }
        env={cell:(0.,0.,0.) for bycountry in country_data.values() for cell in bycountry}
        cells=sorted(env)
        mat=np.full((len(cells),6),.5)
        out=m.country_shadow(bat,"CO",country_data,["MX","CO"],env,
            mat,{cell:i for i,cell in enumerate(cells)},
            [f"Plant{i}" for i in range(6)],[],{"CO":[],"MX":[]})
        self.assertEqual(out["status"],m.STATUS_BAT)
        self.assertEqual(out["test_target_background_cells"],0)


if __name__=="__main__":
    unittest.main()
