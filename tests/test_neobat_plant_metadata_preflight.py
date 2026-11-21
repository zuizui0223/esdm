"""Synthetic-only tests for full NeoBat plant-name metadata gate."""
import unittest
from unittest.mock import patch
from scripts import neobat_plant_metadata_preflight as plant


def rows():
    f=[
      dict(SiteCode='1',RefCode='A',CurrentBatSpecies='Carollia perspicillata',CurrentPlantSpecies='Ficus insipida',Interaction='Frugivory',TrophicGuild='Frugivore'),
      dict(SiteCode='2',RefCode='B',CurrentBatSpecies='Carollia perspicillata',CurrentPlantSpecies='Piper aduncum',Interaction='Frugivory',TrophicGuild='Frugivore'),
      dict(SiteCode='2',RefCode='B',CurrentBatSpecies='Carollia perspicillata',CurrentPlantSpecies='Cecropia peltata',Interaction='Frugivory',TrophicGuild='Frugivore')]
    sites=[dict(SiteCode='1',RefCode='A',Country='Brazil',Precision='Precise',SamplingEffort='NA'),
           dict(SiteCode='2',RefCode='B',Country='Mexico',Precision='Precise',SamplingEffort='NA')]
    return {'records':f,'sites':sites,'references':[{'RefCode':'A'},{'RefCode':'B'}]}


class TestPlantSource(unittest.TestCase):
    def test_network_roster_not_entire_plant_registry(self):
        links,s=plant.target_plant_links(rows())
        self.assertEqual(len(links),3)
        self.assertEqual(s['network_candidates_primary'],1)

    def test_taxonomy_requires_exact_species_match(self):
        with patch.object(plant.base,'get',return_value=b'{"rank":"SPECIES","matchType":"FUZZY","confidence":99,"usageKey":1234}'):
            r=plant.plant_lookup('Ficus insipida')
        self.assertEqual(r['status'],'TAXON_AMBIGUOUS')

    def test_region_counts_are_not_cells_or_citable_download(self):
        def get(url):
            if '/species/match' in url:
                return b'{"rank":"SPECIES","matchType":"EXACT","status":"ACCEPTED","confidence":98,"usageKey":1234}'
            return b'{"count":1000,"facets":[{"field":"COUNTRY","counts":[{"name":"BR","count":20},{"name":"MX","count":30},{"name":"US","count":950}]}]}'
        with patch.object(plant.base,'get',side_effect=get):
            r=plant.plant_lookup('Ficus insipida')
        self.assertEqual(r['regional_records_upper_bound'],50)
        self.assertEqual(r['countries_with_5plus_records'],2)
        self.assertFalse(r['spatial_cell_eligibility_tested'])
        self.assertIsNone(r['GBIF_download_DOI'])

    def test_network_coverage_reports_unevaluated_links(self):
        links=[('B1','Ficus insipida'),('B1','Piper aduncum')]
        rows=[{'plant':'Ficus insipida','status':'GBIF_PLANT_COUNTS_ONLY','countries_with_5plus_records':2},
              {'plant':'Piper aduncum','status':'TAXON_AMBIGUOUS'}]
        r=plant.summarize(links,rows)
        self.assertEqual(r['links_with_2_country_plant_count_screen'],1)
        self.assertEqual(r['distinct_bat_plant_links'],2)
        self.assertFalse(r['DOI_bearing_download_present'])


if __name__=='__main__':
    unittest.main()
