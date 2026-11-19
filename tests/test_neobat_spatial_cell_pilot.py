"""Source-independent schema and bounds tests for the prefit 25/50 km pilot."""
from __future__ import annotations
import unittest
from unittest.mock import patch

from scripts import neobat_spatial_cell_pilot as pilot


class TestSpatialPilot(unittest.TestCase):
    def test_predeclared_14_taxon_roster(self):
        self.assertEqual(len(pilot.BATS),4)
        self.assertEqual(len(pilot.PLANTS),10)
        self.assertEqual(len(set(pilot.BATS+pilot.PLANTS)),14)

    def test_missing_accuracy_is_not_called_high_precision(self):
        self.assertEqual(pilot.label_precision(None),'missing')
        self.assertEqual(pilot.label_precision(''),'missing')
        self.assertEqual(pilot.label_precision(-1),'missing')
        self.assertEqual(pilot.label_precision(12500),'known_le_12_5km')
        self.assertEqual(pilot.label_precision(12501),'known_gt_12_5km')

    def test_cell_projection_and_invalid_coordinate(self):
        x=pilot.spatial_grid(-47.5,-15.5)
        self.assertEqual(len(x),2)
        self.assertEqual(x,pilot.spatial_grid(-47.50001,-15.50001))
        self.assertIsNone(pilot.spatial_grid(float('nan'),0))
        self.assertIsNone(pilot.spatial_grid(190,0))

    def test_source_input_key_and_status_gates(self):
        bat={'records':[{'bat':s,'status':'GBIF_COUNTS_ONLY',
                         'match':{'rank':'SPECIES','usageKey':i+1}}
            for i,s in enumerate(pilot.BATS)]}
        plant={'plants':[{'plant':s,'status':'GBIF_PLANT_COUNTS_ONLY',
                         'match':{'rank':'SPECIES','acceptedUsageKey':i+100}}
            for i,s in enumerate(pilot.PLANTS)]}
        self.assertEqual(len(pilot.choose_taxa(bat,plant)),14)
        plant['plants'][0]['status']='TAXON_AMBIGUOUS'
        with self.assertRaisesRegex(RuntimeError,'TAXON_NOT_ADMITTED_STOP'):
            pilot.choose_taxa(bat,plant)

    def test_one_page_aggregates_no_raw_coordinates_or_doi(self):
        d={'group':'plant','name':'Ficus insipida','taxonKey':123}
        fake={'count':3,'results':[
            {'countryCode':'BR','decimalLongitude':-47.5,'decimalLatitude':-15.5,
             'coordinateUncertaintyInMeters':1000,'datasetKey':'D1','basisOfRecord':'PRESERVED_SPECIMEN'},
            {'countryCode':'BR','decimalLongitude':-47.5,'decimalLatitude':-15.5,
             'coordinateUncertaintyInMeters':None,'datasetKey':'D2','basisOfRecord':'HUMAN_OBSERVATION'},
            {'countryCode':'US','decimalLongitude':-96,'decimalLatitude':38,'datasetKey':'D3'}]}
        with patch.object(pilot,'gbif_get',return_value=fake):
            r=pilot.audit_species(d,pace=0)
        self.assertEqual(r['status'],'CELL_COUNTS_ONLY')
        self.assertEqual(r['country_proxy_records'],2)
        self.assertEqual(r['distinct_25km_cells'],1)
        self.assertEqual(r['known_le_12500m_25km_cells'],1)
        self.assertEqual(r['coordinate_uncertainty_missing'],1)
        self.assertEqual(r['country_summary']['BR']['independent_datasetKeys'],2)
        self.assertNotIn('decimalLatitude',str(r))
        self.assertIsNone(r['citable_GBIF_download_DOI'])
        self.assertFalse(r['independent_training_test_folds_certified'])

    def test_api_limit_stops_without_truncation(self):
        with patch.object(pilot,'gbif_get',return_value={'count':100001,'results':[{}]}):
            r=pilot.audit_species({'group':'bat','name':'Carollia perspicillata','taxonKey':1},pace=0)
        self.assertEqual(r['status'],'SPATIAL_PREFLIGHT_STOP')
        self.assertIn('API_100K_LIMIT_STOP',r['error'])


if __name__=='__main__':
    unittest.main()
