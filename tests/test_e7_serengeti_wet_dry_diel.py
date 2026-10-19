"""Synthetic checks for E7. No independent Serengeti response is opened here."""
import json
import zipfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts import e7_serengeti_wet_dry_diel as e7


class E7Tests(unittest.TestCase):
    def test_calendar_time_and_source_splits_are_frozen(self):
        self.assertEqual(e7.DISCOVERY,(1,2,3,4,5))
        self.assertEqual(e7.VALIDATION,(6,7,8,9,10,11))
        self.assertEqual(e7.climatological_phase(11),"wet")
        self.assertEqual(e7.climatological_phase(4),"wet")
        self.assertEqual(e7.climatological_phase(6),"dry")
        self.assertIsNone(e7.climatological_phase(5))
        self.assertIsNone(e7.climatological_phase(10))
        self.assertEqual(e7.water_year(datetime(2018,11,1)),2018)
        self.assertEqual(e7.water_year(datetime(2019,9,15)),2018)
        self.assertEqual(e7.clock_period(23),"night")
        self.assertEqual(e7.clock_period(2),"night")
        self.assertEqual(e7.clock_period(12),"midday")
        self.assertIsNone(e7.clock_period(18))

    def test_category_restrictions_and_lion_sex_relabeling(self):
        self.assertEqual(e7.normal_name("lionFemale"),"lion")
        self.assertEqual(e7.normal_name("lionMale"),"lion")
        self.assertEqual(e7.normal_name("gazelleThomsons"),"gazelleThomsons")
        self.assertIsNone(e7.normal_name("human"))
        self.assertIsNone(e7.normal_name("empty"))
        self.assertIsNone(e7.normal_name("ostrich"))
        self.assertIsNone(e7.normal_name("otherBird"))

    def test_sequences_not_individual_images(self):
        with TemporaryDirectory() as d:
            archive=Path(d)/"SnapshotSerengetiS01.json.zip"
            categories=[
                {"id":i,"name":name} for i,name in enumerate((
                    "empty","human","wildebeest","zebra","lionFemale","lionMale",
                    "gazelleThomsons","ostrich","buffalo","giraffe","warthog"))
            ]
            images=[]
            annotations=[]
            n=0
            for period,dt in (("wet","2010-12-15 23:10:00"),
                              ("dry","2011-07-15 12:10:00")):
                for species, cat in (("zebra",3),("wildebeest",2)):
                    seq=f"{period}-{species}"
                    for frame in (1,2,3):
                        n+=1
                        images.append({"id":f"i{n}","seq_id":seq,"location":"C14","datetime":dt})
                        annotations.append({"id":n,"image_id":f"i{n}","category_id":cat})
            doc={"info":{"version":"2.0"},"categories":categories,"images":images,"annotations":annotations}
            with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as z:
                z.writestr("sample.json",json.dumps(doc))
            cnt=Counter(); occ=defaultdict(set); src=defaultdict(set)
            summary=e7.parse_season(archive,1,cnt,occ,src)
            self.assertEqual(summary["images"],12)
            self.assertEqual(summary["annotations"],12)
            self.assertEqual(summary["valid_focal_hour_sequences"],4)
            self.assertEqual(cnt[("C14",2010,"wet","zebra","night")],1)
            self.assertEqual(cnt[("C14",2010,"dry","wildebeest","midday")],1)
            self.assertEqual(len(occ["zebra"]),1)
            self.assertEqual(src[("C14",2010,"dry")],{1})

    def test_only_matched_camera_hydrological_year_and_positive_time_bins(self):
        counts=Counter();support=defaultdict(set)
        for j in range(6):
            for water in (2010,2011):
                loc=f"S{j}"
                for phase in ("wet","dry"):
                    a,b,c,d=(5,2,2,5) if phase=="wet" else (2,5,5,2)
                    counts[(loc,water,phase,"zebra","night")]=a
                    counts[(loc,water,phase,"zebra","midday")]=b
                    counts[(loc,water,phase,"wildebeest","night")]=c
                    counts[(loc,water,phase,"wildebeest","midday")]=d
                    support[(loc,water,phase)].update((1,2,3))
        pair=e7.per_pair(counts,support,"zebra","wildebeest")
        self.assertEqual(pair["matched_distinct_sites"],6)
        self.assertEqual(pair["matched_site_years"],12)
        self.assertEqual(pair["supporting_original_seasons"],3)
        self.assertAlmostEqual(pair["wet_odds"],6.25)
        self.assertAlmostEqual(pair["dry_odds"],0.16)
        self.assertTrue(pair["rank_reversal_in_recorded_diel_odds"])
        self.assertTrue(pair["rank_reversal_stable_under_site_deletion"])
        self.assertTrue(pair["leave_one_site_out_all_computable"])

    def test_inadequate_site_year_support_declines_to_fit(self):
        c=Counter();f=defaultdict(set)
        for loc in ("A","B"):
            for phase in ("wet","dry"):
                for name,night,midday in (("zebra",5,2),("wildebeest",2,5)):
                    c[(loc,2018,phase,name,"night")]=night
                    c[(loc,2018,phase,name,"midday")]=midday
                f[(loc,2018,phase)].update((1,2,3))
        pair=e7.per_pair(c,f,"zebra","wildebeest")
        self.assertEqual(pair["status"],"INSUFFICIENT_MATCHED_CAMERA_YEARS")
        self.assertIsNone(pair["relative_shift"])

    def test_panel_comes_from_discovery_presence_not_diel_effect(self):
        cnt=Counter()
        occ=defaultdict(set)
        for name,siteyears in {
            "zebra":(("S1",2010),("S1",2011),("S2",2011)),
            "wildebeest":(("S2",2011),("S3",2011)),
            "lion":(("S4",2011),),
        }.items():
            occ[name].update(siteyears)
            cnt[("S1",2010,"wet",name,"night")]=100 if name=="lion" else 2
        ranked=e7.choose_discovery_panel(cnt,occ)
        self.assertEqual(ranked[:3],["zebra","wildebeest","lion"])
        self.assertEqual(e7.TOP_N,12)


if __name__=="__main__":
    unittest.main()
