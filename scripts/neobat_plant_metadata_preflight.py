"""Plant taxon and GBIF count-only gate for the 26-network-candidate NeoBat frugivores.

No plant occurrence coordinates are downloaded; this script cannot fit an SDM.
"""
from __future__ import annotations
import argparse, json, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode

from scripts import neobat_gbif_metadata_preflight as base


def target_plant_links(tables):
    source=base.audit(tables)
    bats={r['bat'] for r in source['species'] if r['primary_candidate']}
    rows=tables['records']
    links={(r['CurrentBatSpecies'],r['CurrentPlantSpecies'])
           for r in rows if r['Interaction']=='Frugivory'
           and r['TrophicGuild']=='Frugivore'
           and r['CurrentBatSpecies'] in bats
           and base.binomial(r['CurrentPlantSpecies'])}
    return sorted(links),source


def plant_lookup(name):
    m=json.loads(base.get('https://api.gbif.org/v1/species/match?'+
                          urlencode({'name':name,'strict':'true'})))
    item={'plant':name,'match':{k:m.get(k) for k in (
        'matchType','rank','status','scientificName','confidence',
        'usageKey','acceptedUsageKey')}}
    key=m.get('acceptedUsageKey') or m.get('usageKey')
    if m.get('matchType')!='EXACT' or m.get('rank')!='SPECIES' or m.get('confidence',0)<90 or not key:
        item['status']='TAXON_AMBIGUOUS'
        return item
    params=urlencode({'taxonKey':key,'hasCoordinate':'true',
                      'hasGeospatialIssue':'false','year':'2000,2025',
                      'occurrenceStatus':'PRESENT','limit':0,
                      'facet':'country','facetLimit':200})
    search=json.loads(base.get('https://api.gbif.org/v1/occurrence/search?'+params))
    counts=next((f.get('counts',[]) for f in search.get('facets',[])
                 if f.get('field','').upper()=='COUNTRY'),[])
    relevant={r['name']:r['count'] for r in counts if r['name'] in base.LATAM}
    item.update(status='GBIF_PLANT_COUNTS_ONLY',world_records=search.get('count'),
                regional_records_upper_bound=sum(relevant.values()),
                regional_country_counts=relevant,
                countries_with_5plus_records=sum(v>=5 for v in relevant.values()),
                target_region_not_spatially_clipped=True,
                spatial_cell_eligibility_tested=False,
                GBIF_download_DOI=None)
    return item


def summarize(links,plant_rows):
    by={r['plant']:r for r in plant_rows}
    allowed={p for p,r in by.items()
             if r['status']=='GBIF_PLANT_COUNTS_ONLY' and
             r['countries_with_5plus_records']>=2}
    exact={p for p,r in by.items() if r['status']=='GBIF_PLANT_COUNTS_ONLY'}
    bats=sorted({b for b,p in links})
    species=[{'bat':b,'original_links':sum(bb==b for bb,p in links),
              'links_with_exact_plant_match':sum(bb==b and p in exact for bb,p in links),
              'links_with_two_country_plant_count_screen':sum(bb==b and p in allowed for bb,p in links)}
             for b in bats]
    status_counts=dict(Counter(r['status'] for r in plant_rows))
    missing=sum(r['status'] in ('REMOTE_STOP','NOT_QUERIED_API_CIRCUIT_STOP') for r in plant_rows)
    return {'status':'GBIF_PLANT_METADATA_INCOMPLETE' if missing else 'GBIF_PLANT_METADATA_ONLY',
            'created_utc':datetime.now(timezone.utc).isoformat(),
            'bat_network_candidates':len(bats),'distinct_original_plant_name_strings':len(by),
            'distinct_bat_plant_links':len(links),
            'plant_status_counts':status_counts,
            'plant_exact_match_count':len(exact),
            'plant_2_country_raw_count_screen':len(allowed),
            'links_with_exact_plant_match':sum(p in exact for b,p in links),
            'links_with_2_country_plant_count_screen':sum(p in allowed for b,p in links),
            'source_response_independent_spatial_folds_not_checked':True,
            'DOI_bearing_download_present':False,
            'temporal_fruit_abundance_not_observed':True,
            'ecological_result':None,'per_bat':species,'plants':plant_rows}


def main():
    pa=argparse.ArgumentParser()
    pa.add_argument('--out',default='build/neobat/plant_search_preflight.json')
    args=pa.parse_args()
    out=Path(args.out);out.parent.mkdir(parents=True,exist_ok=True)
    t={};source={}
    try:
        for k in base.FILES: t[k],source[k]=base.read_source(k)
        links,audit=target_plant_links(t)
        names=sorted({p for b,p in links})
        print('Plant name strings:',len(names),'bat-plant links:',len(links),flush=True)
        results=[]
        consecutive_remote_stops=0
        for i,name in enumerate(names,1):
            try:
                r=plant_lookup(name)
            except Exception as exc:
                r={'plant':name,'status':'REMOTE_STOP','error':str(exc)[:220]}
            results.append(r)
            consecutive_remote_stops=(consecutive_remote_stops+1) if r['status']=='REMOTE_STOP' else 0
            if consecutive_remote_stops>=5:
                results.extend({'plant':p,'status':'NOT_QUERIED_API_CIRCUIT_STOP'} for p in names[i:])
                print('API_CIRCUIT_STOP after 5 consecutive errors; remaining named but not queried',flush=True)
                break
            if i%20==0 or i==len(names):
                counts=Counter(x['status'] for x in results)
                print(f'PLANT {i}/{len(names)} status={dict(counts)}',flush=True)
            time.sleep(0.18)
        receipt=summarize(links,results)
        receipt['source_sha256']={k:v['sha256'] for k,v in source.items()}
    except Exception as exc:
        receipt={'status':'PLANT_PREFLIGHT_SOURCE_STOP','error':str(exc)[:240],
                 'ecological_result':None,'GBIF_download_DOI':None}
    out.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:receipt.get(k) for k in (
        'status','bat_network_candidates','distinct_original_plant_name_strings',
        'plant_exact_match_count','plant_2_country_raw_count_screen',
        'links_with_exact_plant_match','links_with_2_country_plant_count_screen')},indent=2),flush=True)
    return 0 if receipt['status']=='GBIF_PLANT_METADATA_ONLY' else 3


if __name__=='__main__': raise SystemExit(main())
