/* NeoBat independent-source leave-country-out link transfer, exploratory source-only.
 * Does not download GBIF responses, infer absences, or fit an SDM.
 * Usage: node scripts/neobat_crosscountry_link_transfer.mjs records.csv sites.csv result.json
 * Run --self-test to test exact degree preservation without biological input.
 */
import fs from 'node:fs';
import assert from 'node:assert/strict';

function parseCSV(s) {
  const data=[]; let row=[],field="",q=false;
  for (let i=0;i<s.length;i++) {
    const c=s[i];
    if (c==='"') { if(q&&s[i+1]==='"'){field+='"';i++;}else q=!q; }
    else if(c===','&&!q){row.push(field);field='';}
    else if((c==='\n'||c==='\r')&&!q){if(c==='\r'&&s[i+1]==='\n')i++;row.push(field);if(row.length>1||row[0])data.push(row);row=[];field='';}
    else field+=c;
  }
  if(field||row.length){row.push(field);data.push(row);}
  const [head,...rows]=data;
  if(!head||rows.length===0) throw Error('CSV_SCHEMA_OR_EMPTY_STOP');
  return rows.map(r=>Object.fromEntries(head.map((h,i)=>[h,r[i]??''])));
}
function pair(b,p){return b+'\u001f'+p;}
function XorShift(seed){
  let x=seed>>>0;
  return ()=>{x^=x<<13;x^=x>>>17;x^=x<<5;return (x>>>0)/4294967296;};
}
function hasLegal(edges,set){
  for(let i=0;i<edges.length;i++)for(let j=i+1;j<edges.length;j++){
    const [a,x]=edges[i],[b,y]=edges[j];
    if(a!==b&&x!==y&&!set.has(pair(a,y))&&!set.has(pair(b,x))) return true;
  }
  return false;
}
function shuffleGraph(edges,set,rand,attempts){
  let accepted=0,E=edges.length;
  for(let k=0;k<attempts;k++){
    let i=Math.floor(rand()*E),j=Math.floor(rand()*E);
    if(i===j)continue;
    let [a,x]=edges[i],[b,y]=edges[j];
    if(a===b||x===y)continue;
    let v=pair(a,y),w=pair(b,x);
    if(set.has(v)||set.has(w))continue;
    set.delete(pair(a,x));set.delete(pair(b,y));set.add(v);set.add(w);
    edges[i]=[a,y];edges[j]=[b,x];accepted++;
  }
  return accepted;
}
function degree(e){
  const bat=new Map(),plant=new Map();
  for(const [b,p] of e){bat.set(b,(bat.get(b)||0)+1);plant.set(p,(plant.get(p)||0)+1);}
  return JSON.stringify([[...bat.entries()].sort(),[...plant.entries()].sort()]);
}
function analyze(records,sites,{seed=20261119,reps=999}={}){
  const siteBy=new Map(sites.map(s=>[s.SiteCode,s]));
  if(siteBy.size!==sites.length)throw Error('DUPLICATED_SITECODE_STOP');
  const bin=x=>/^[A-Z][A-Za-z-]+ [a-z-]+$/.test(x||"");
  const raw=records.filter(r=>r.Interaction==='Frugivory'&&r.TrophicGuild==='Frugivore'&&
    bin(r.CurrentBatSpecies)&&bin(r.CurrentPlantSpecies)&&siteBy.has(r.SiteCode));
  if(raw.some(r=>siteBy.get(r.SiteCode).RefCode!==r.RefCode))throw Error('SITE_REF_CONFLICT_STOP');
  const byBat=new Map();
  for(const r of raw){let arr=byBat.get(r.CurrentBatSpecies)||[];arr.push(r);byBat.set(r.CurrentBatSpecies,arr);}
  const primary=[...byBat.entries()].filter(([b,rs])=>
    new Set(rs.map(x=>x.CurrentPlantSpecies)).size>=3&&
    new Set(rs.map(x=>x.RefCode)).size>=2&&
    new Set(rs.map(x=>siteBy.get(x.SiteCode).Country)).size>=2).map(([b])=>b).sort();
  const primarySet=new Set(primary),valid=raw.filter(x=>primarySet.has(x.CurrentBatSpecies));
  const countries=[...new Set(valid.map(x=>siteBy.get(x.SiteCode).Country))].sort();
  const countrySummaries=[],qualified=[];
  for(const country of countries){
    const testRows=valid.filter(r=>siteBy.get(r.SiteCode).Country===country);
    const testRefs=new Set(testRows.map(r=>r.RefCode));
    const trainRows=valid.filter(r=>
      siteBy.get(r.SiteCode).Country!==country&&!testRefs.has(r.RefCode));
    const trainBat=new Set(trainRows.map(r=>r.CurrentBatSpecies));
    const trainPlant=new Set(trainRows.map(r=>r.CurrentPlantSpecies));
    const trainRefs=new Map();
    for(const r of trainRows){
      const k=pair(r.CurrentBatSpecies,r.CurrentPlantSpecies),set=trainRefs.get(k)||new Set();
      set.add(r.RefCode);trainRefs.set(k,set);
    }
    const testEligible=testRows.filter(r=>trainBat.has(r.CurrentBatSpecies)&&trainPlant.has(r.CurrentPlantSpecies));
    const testEdges=[...new Set(testEligible.map(r=>pair(r.CurrentBatSpecies,r.CurrentPlantSpecies)))]
      .sort().map(k=>k.split('\u001f'));
    const testSet=new Set(testEdges.map(([b,p])=>pair(b,p)));
    const nbat=new Set(testEdges.map(x=>x[0])).size,nplants=new Set(testEdges.map(x=>x[1])).size;
    const nrefs=new Set(testEligible.map(x=>x.RefCode)).size;
    const legalSwap=hasLegal(testEdges,testSet);
    const eligible=nbat>=2&&nplants>=3&&nrefs>=2&&testEdges.length>=6&&legalSwap;
    const covered=(minref)=>testEdges.filter(([b,p])=>(trainRefs.get(pair(b,p))?.size||0)>=minref).length;
    const summary={
      country,test_rows:testRows.length,test_publication_n:testRefs.size,
      train_rows:trainRows.length,eligible_test_rows:testEligible.length,
      heldout_edges:new Set(testRows.map(r=>pair(r.CurrentBatSpecies,r.CurrentPlantSpecies))).size,
      known_node_test_edges:testEdges.length,known_bats:nbat,known_plants:nplants,
      test_refs:nrefs,legal_degree_swap:legalSwap,qualifies:eligible,
      observed_repeated_links:covered(1),observed_repeated_2ref_links:covered(2),
      observed_fraction:testEdges.length?covered(1)/testEdges.length:null
    };
    countrySummaries.push(summary);
    if(eligible)qualified.push({country,summary,trainRefs,edges:testEdges,set:testSet});
  }
  if(qualified.length===0)return{status:'INSUFFICIENT_COUNTRIES_FOR_NULL',countries:countrySummaries,ecological_result:null};
  const rand=XorShift(seed);let totalAccepted=0;
  for(const item of qualified){
    item.edges=item.edges.map(x=>[...x]);item.set=new Set(item.edges.map(x=>pair(...x)));
    totalAccepted+=shuffleGraph(item.edges,item.set,rand,100*item.edges.length);
  }
  const nullDraws=[],byCountryNull=new Map(qualified.map(item=>[item.country,{sum:0,sum2:0}]));
  for(let k=0;k<reps;k++){
    let means=[],means2=[];
    for(const item of qualified){
      totalAccepted+=shuffleGraph(item.edges,item.set,rand,20*item.edges.length);
      const n=item.edges.length;
      const a=item.edges.filter(([b,p])=>(item.trainRefs.get(pair(b,p))?.size||0)>=1).length/n;
      const b=item.edges.filter(([b,p])=>(item.trainRefs.get(pair(b,p))?.size||0)>=2).length/n;
      means.push(a);means2.push(b);
      const c=byCountryNull.get(item.country);c.sum+=a;c.sum2+=b;
    }
    nullDraws.push([means.reduce((a,b)=>a+b,0)/means.length,means2.reduce((a,b)=>a+b,0)/means2.length]);
  }
  const obs=qualified.reduce((s,x)=>s+x.summary.observed_repeated_links/x.edges.length,0)/qualified.length;
  const obs2=qualified.reduce((s,x)=>s+x.summary.observed_repeated_2ref_links/x.edges.length,0)/qualified.length;
  const nv=nullDraws.map(x=>x[0]),nv2=nullDraws.map(x=>x[1]);
  const mu=nv.reduce((a,b)=>a+b,0)/reps,mu2=nv2.reduce((a,b)=>a+b,0)/reps;
  const sorted=[...nv].sort((a,b)=>a-b);
  for(const c of countrySummaries){
    if(!c.qualifies)continue;
    const n=byCountryNull.get(c.country);
    c.null_mean_fraction=n.sum/reps;
    c.null_mean_2ref_fraction=n.sum2/reps;
    c.country_difference=c.observed_fraction-c.null_mean_fraction;
  }
  return{
    status:'EXPLORATORY_SOURCE_ONLY',
    seed,replicates:reps,species_candidates:primary.length,
    country_source_total:countries.length,countries_eligible:qualified.length,
    n_test_edges:qualified.reduce((s,x)=>s+x.summary.known_node_test_edges,0),
    n_test_references_sum:qualified.reduce((s,x)=>s+x.summary.test_refs,0),
    primary:{
      observed:obs,null_mean:mu,difference:obs-mu,
      p_upper_monte_carlo:(1+nv.filter(x=>x>=obs-1e-12).length)/(reps+1),
      null_q025:sorted[Math.floor(0.025*(sorted.length-1))],
      null_q50:sorted[Math.floor(0.5*(sorted.length-1))],
      null_q975:sorted[Math.floor(0.975*(sorted.length-1))]
    },
    two_reference_sensitivity:{
      observed:obs2,null_mean:mu2,difference:obs2-mu2,
      p_upper_monte_carlo:(1+nv2.filter(x=>x>=obs2-1e-12).length)/(reps+1)
    },
    accepted_swaps_total:totalAccepted,per_country:countrySummaries,
    no_absences_assumed:true,independent_external_interactions:false,
    gbif_presence_prediction:null,ecological_causality:null
  };
}
function selfTest(){
  const e=[['a','x'],['b','y'],['a','z'],['c','x'],['c','z']];
  const d=degree(e),rand=XorShift(12345),s=new Set(e.map(([b,p])=>pair(b,p)));
  assert.ok(hasLegal(e,s));
  assert.ok(shuffleGraph(e,s,rand,1000)>0);
  assert.equal(degree(e),d);
  assert.equal(s.size,e.length);
  assert.equal(parseCSV('a,b\n"z,q",1\n')[0].a,'z,q');
  process.stdout.write('SELF_TEST_PASS\n');
}
if(process.argv.includes('--self-test'))selfTest();
else {
  const [recFile,siteFile,outFile]=process.argv.slice(2);
  if(!recFile||!siteFile||!outFile)throw Error('Usage: script records.csv sites.csv result.json');
  const R=parseCSV(fs.readFileSync(recFile).toString('latin1'));
  const S=parseCSV(fs.readFileSync(siteFile).toString('latin1'));
  const result=analyze(R,S);
  fs.mkdirSync((await import('node:path')).dirname(outFile),{recursive:true});
  fs.writeFileSync(outFile,JSON.stringify(result,null,2)+'\n');
  process.stdout.write(JSON.stringify({
    status:result.status,countries_eligible:result.countries_eligible,
    species_candidates:result.species_candidates,n_test_edges:result.n_test_edges,
    primary:result.primary,two_reference_sensitivity:result.two_reference_sensitivity
  },null,2)+'\n');
}
