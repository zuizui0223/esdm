"""NeoBat source audit and GBIF metadata-only screening. No SDM fit or inference."""
from __future__ import annotations
import argparse, csv, hashlib, io, json, re, time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

REPO='gflorezm/NeoBat_Interactions'
COMMIT='d25292d19be32a85a21c60384a3f2d818e8081de'
FILES={'records':('Data/NeoBat_Interactions_Records.csv','71f179a152a262d7a98d7bb4e633cf136bc39f98'),
       'sites':('Data/NeoBat_Interactions_Sites.csv','f9672a8b5542b8f4ecd3434ca798756f865df541'),
       'references':('Data/NeoBat_Interactions_References.csv','9061aa7a2b2f44a1aa23273a87cba6183af823b1')}
LATAM={'AR','BO','BR','BZ','CL','CO','CR','CU','CW','DO','EC','GF','GT','GY','HN','HT','JM','MX','NI','PA','PE','PR','PY','SR','SV','TT','UY','VE','BS'}


def get(url):
    req=Request(url,headers={'User-Agent':'esdm-neobat-science-preflight/0.1','Accept':'application/json'})
    with urlopen(req,timeout=35) as response: return response.read()


def read_source(name):
    path,sha=FILES[name]
    url=f'https://raw.githubusercontent.com/{REPO}/{COMMIT}/{path}'
    raw=get(url)
    blob=hashlib.sha1(f'blob {len(raw)}\0'.encode()+raw).hexdigest()
    if blob!=sha: raise RuntimeError(f'IMMUTABLE_SOURCE_MISMATCH_{name}')
    parsed=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if not parsed: raise RuntimeError(f'EMPTY_SOURCE_{name}')
    return parsed, {'url':url,'git_blob_sha':blob,'sha256':hashlib.sha256(raw).hexdigest(),'rows':len(parsed)}


def binomial(s): return bool(re.fullmatch(r'[A-Z][A-Za-z-]+ [a-z-]+',s or ''))


def audit(tables):
    rec, sites, refs=tables['records'],tables['sites'],tables['references']
    si={s['SiteCode']:s for s in sites}; ri={r['RefCode']:r for r in refs}
    if len(si)!=len(sites) or len(ri)!=len(refs): raise RuntimeError('DUPLICATED_SITE_OR_REFERENCE_KEY')
    fruit=[r for r in rec if r['Interaction']=='Frugivory']
    if any(r['SiteCode'] not in si or r['RefCode'] not in ri for r in fruit): raise RuntimeError('UNJOINED_SOURCE_KEY')
    conflicts=[r['SiteCode'] for r in fruit if r['RefCode']!=si[r['SiteCode']]['RefCode']]
    resolved=[r for r in fruit if binomial(r['CurrentBatSpecies']) and binomial(r['CurrentPlantSpecies'])]
    by=defaultdict(list)
    for r in resolved: by[r['CurrentBatSpecies']].append(r)
    species=[]
    for bat,rs in by.items():
        ps={r['CurrentPlantSpecies'] for r in rs}; refs={r['RefCode'] for r in rs}
        src={r['SiteCode'] for r in rs}; countries={si[k]['Country'] for k in src}
        network=len(ps)>=3 and len(refs)>=2 and len(countries)>=2
        primary=all(r['TrophicGuild']=='Frugivore' for r in rs)
        species.append({'bat':bat,'fruit_rows':len(rs),'plant_strings':len(ps),
                        'references':len(refs),'source_sites':len(src),'countries':len(countries),
                        'precise_sites':sum(si[k]['Precision']=='Precise' for k in src),
                        'network_gate':network,'primary_frugivore':primary,
                        'primary_candidate':network and primary})
    species.sort(key=lambda s:(-s['references'],-s['fruit_rows'],s['bat']))
    fs={r['SiteCode'] for r in fruit}
    return {'status':'INTERACTION_SOURCE_ONLY','source_commit':COMMIT,
            'total_rows':len(rec),'frugivory_rows':len(fruit),
            'interaction_counts':dict(Counter(r['Interaction'] for r in rec)),
            'fruit_guild_counts':dict(Counter(r['TrophicGuild'] for r in fruit)),
            'binomial_looking_fruit_rows':len(resolved),
            'fruit_sites':len(fs),'fruit_refs':len({r['RefCode'] for r in fruit}),
            'fruit_site_precision_unknown':sum(si[k]['Precision']!='Precise' for k in fs),
            'fruit_site_sampling_effort_missing':sum(si[k]['SamplingEffort'] in ('','NA') for k in fs),
            'source_ref_conflict_count':len(conflicts),
            'network_candidates_all':sum(x['network_gate'] for x in species),
            'network_candidates_primary':sum(x['primary_candidate'] for x in species),
            'species':species,'ecological_result':None}


def gbif_screen(rows):
    screened=[]
    for row in rows:
        if not row['primary_candidate']: continue
        name=row['bat']; result={'bat':name,'status':'UNQUERIED'}
        try:
            m=json.loads(get('https://api.gbif.org/v1/species/match?'+urlencode({'name':name,'strict':'true'})))
            result['match']={k:m.get(k) for k in ('matchType','rank','status','confidence','scientificName','usageKey','acceptedUsageKey')}
            key=m.get('acceptedUsageKey') or m.get('usageKey')
            if m.get('rank')!='SPECIES' or m.get('matchType')!='EXACT' or m.get('confidence',0)<90 or not key:
                result['status']='TAXON_AMBIGUOUS';continue
            q=urlencode({'taxonKey':key,'hasCoordinate':'true','hasGeospatialIssue':'false',
                         'year':'2000,2025','occurrenceStatus':'PRESENT','limit':0,'facet':'country','facetLimit':200})
            x=json.loads(get('https://api.gbif.org/v1/occurrence/search?'+q))
            fac=next((f.get('counts',[]) for f in x.get('facets',[]) if f.get('field','').upper()=='COUNTRY'),[])
            regional={p['name']:p['count'] for p in fac if p['name'] in LATAM}
            result.update(status='GBIF_COUNTS_ONLY',world_records=x.get('count'),
                regional_records_upper_bound=sum(regional.values()),
                regional_country_counts=regional,
                countries_with_5plus_records=sum(v>=5 for v in regional.values()),
                country_facet_truncated=len(fac)>=200,
                spatial_25km_cells_verified=False, GBIF_download_DOI=None)
        except Exception as exc:
            result.update(status='REMOTE_STOP',error=str(exc)[:220])
        finally:
            screened.append(result)
            print(f"GBIF {name}: {result['status']}",flush=True)
            time.sleep(0.2)
    return {'status':'GBIF_SEARCH_METADATA_ONLY','updated_utc':datetime.now(timezone.utc).isoformat(),
            'evaluated_candidates':len(screened),
            'search_count_pass':sum(r['status']=='GBIF_COUNTS_ONLY' for r in screened),
            'taxon_ambiguous':sum(r['status']=='TAXON_AMBIGUOUS' for r in screened),
            'remote_stop':sum(r['status']=='REMOTE_STOP' for r in screened),
            'GBIF_download_DOI':None,'spatial_cell_eligibility_tested':False,
            'bat_occurrences_downloaded':False,'plant_occurrences_downloaded':False,
            'ecological_result':None,'records':screened}


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='build/neobat');p.add_argument('--gbif',action='store_true')
    args=p.parse_args();o=Path(args.out);o.mkdir(parents=True,exist_ok=True)
    try:
        tbl={}; sources={}
        for k in FILES: tbl[k],sources[k]=read_source(k)
        r=audit(tbl);r['sources']=sources
    except Exception as exc:
        (o/'source_preflight.json').write_text(json.dumps({'status':'SOURCE_STOP','error':str(exc),'ecological_result':None},indent=2)+'\n')
        raise
    (o/'source_preflight.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print('NETWORK:',json.dumps({k:r[k] for k in ('frugivory_rows','network_candidates_all','network_candidates_primary','source_ref_conflict_count')}),flush=True)
    if args.gbif:
        g=gbif_screen(r['species'])
        (o/'gbif_search_preflight.json').write_text(json.dumps(g,ensure_ascii=False,indent=2)+'\n')
        print('GBIF:',json.dumps({k:g[k] for k in ('evaluated_candidates','search_count_pass','taxon_ambiguous','remote_stop')}),flush=True)
        if g['remote_stop']: return 3
    return 0


if __name__=='__main__': raise SystemExit(main())
