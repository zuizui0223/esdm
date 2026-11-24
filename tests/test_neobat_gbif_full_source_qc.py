"""Synthetic-only full GBIF TSV QC tests. No network, real rows, or DOI POST."""
from __future__ import annotations
import pathlib
import tempfile
import unittest
import zipfile
from unittest.mock import patch

from scripts import neobat_gbif_full_source_qc as qc

HEADER=["gbifID","datasetKey","occurrenceID","speciesKey","taxonKey","countryCode",
        "decimalLatitude","decimalLongitude","coordinateUncertaintyInMeters",
        "year","basisOfRecord"]

def row(gid,key="101",taxon="101",country="BR",year="2024",precision="1000",ds="D1",eid="EV1",lon="-50",lat="-12"):
    x=dict(zip(HEADER,[gid,ds,eid,key,taxon,country,lat,lon,precision,year,"HUMAN_OBSERVATION"]))
    return x

def make_file(rows,header=HEADER):
    out=tempfile.TemporaryDirectory()
    target=pathlib.Path(out.name)/"test.zip"
    with zipfile.ZipFile(target,"w",compression=zipfile.ZIP_DEFLATED) as z:
        text="\t".join(header)+"\n"
        for r in rows:text+="\t".join(str(r.get(k,"")) for k in header)+"\n"
        z.writestr("source.csv",text)
    return out,target,{"zip_entry_name":"source.csv","header_columns":header}

class TestFullSourceQC(unittest.TestCase):
    def test_source_header_bound_and_malformed(self):
        self.assertTrue(qc.source_header_matches(HEADER,HEADER))
        with self.assertRaisesRegex(RuntimeError,"SOURCE_TSV_HEADER_MISMATCH"):
            qc.source_header_matches(list(reversed(HEADER)),HEADER)
        with self.assertRaisesRegex(RuntimeError,"SOURCE_REQUIRED_FIELDS_MISSING"):
            qc.source_header_matches(["gbifID"],["gbifID"])

    def test_full_row_qc_dedupe_and_species_key(self):
        rows=[
          row("10",ds="D1",eid="E1",precision="1000"),
          row("11",ds="D2",eid="E2",precision=""),
          row("11",ds="D2",eid="E2",precision=""), # duplicate gbif ID
          row("12",ds="D1",eid="E1",precision="14000"), # repeated source event ID, distinct gbif ID
          row("13",key="999",taxon="101"), # unmatched speciesKey, conflicting taxonKey
          row("14",year="1990")
        ]
        temp,path,source=make_file(rows)
        try:
            with patch.object(qc,"spatial_grid",side_effect=lambda lon,lat: ((1,2),(0,1))):
                r=qc.quality_counts_for_archive(path,group="bat",source=source,
                    accepted={"101":"Bat species"},expected_count=len(rows))
        finally: temp.cleanup()
        self.assertEqual(r["full_archive_rows_checked"],6)
        self.assertEqual(r["valid_source_rows"],3)
        self.assertEqual(r["quality_breakdown"]["duplicate_gbif_id"],1)
        self.assertEqual(r["quality_breakdown"]["unmatched_species_key"],1)
        self.assertEqual(r["quality_breakdown"]["taxon_key_contradiction"],1)
        self.assertEqual(r["quality_breakdown"]["year_outside_or_missing"],1)
        self.assertEqual(r["duplicate_dataset_occurrence_id_count"],1)
        self.assertEqual(r["species_country_summary"][0]["recorded_25km_cells"],1)
        self.assertEqual(r["species_country_summary"][0]["precision_le12500m_25km_cells"],1)
        self.assertEqual(r["species_country_summary"][0]["source_datasets"],2)
        self.assertIsNone(r["M3_minus_M1"])
        self.assertNotIn("decimalLongitude",str(r))

    def test_raw_archive_count_mismatch_stops(self):
        temp,path,source=make_file([row("1")])
        try:
            with patch.object(qc,"spatial_grid",return_value=((0,1),(0,1))):
                with self.assertRaisesRegex(RuntimeError,"ARCHIVE_GBIF_RECORD_DENOMINATOR_MISMATCH"):
                    qc.quality_counts_for_archive(path,group="bat",source=source,
                                                   accepted={"101":"Bat species"},expected_count=2)
        finally:temp.cleanup()

    def test_invalid_country_and_coordinates_not_used(self):
        rows=[row("1",country="USA"),row("2",lat="nan"),row("3",country="BR")]
        temp,path,source=make_file(rows)
        try:
            def geom(lon,lat):
                return None if not (abs(lat)<90 and abs(lon)<180) else ((1,1),(0,0))
            with patch.object(qc,"spatial_grid",side_effect=geom):
                r=qc.quality_counts_for_archive(path,group="plant",source=source,
                    accepted={"101":"Plant species"},expected_count=3)
        finally:temp.cleanup()
        self.assertEqual(r["quality_breakdown"]["country_malformed"],1)
        self.assertEqual(r["quality_breakdown"]["coordinate_invalid"],1)
        self.assertEqual(r["valid_source_rows"],1)

    def test_taxon_roster_gate(self):
        bat={"records":[{"bat":str(i),"status":"GBIF_COUNTS_ONLY",
                         "match":{"usageKey":i+1}} for i in range(26)]}
        plant={"plants":[{"plant":str(i),"status":"GBIF_PLANT_COUNTS_ONLY",
                          "match":{"usageKey":i+100}} for i in range(255)]}
        got=qc.name_map(bat,plant)
        self.assertEqual(len(got["bat"]),26)
        self.assertEqual(len(got["plant"]),255)
        plant["plants"][0]["match"]["usageKey"]=101
        with self.assertRaisesRegex(RuntimeError,"SOURCE_TAXON_KEY_COLLISION"):
            qc.name_map(bat,plant)

if __name__=="__main__":
    unittest.main()
