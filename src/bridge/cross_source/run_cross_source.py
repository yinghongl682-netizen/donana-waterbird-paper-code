"""Actual-date cross-source analysis. Read-only native inputs; branch-confined outputs."""
from pathlib import Path
import pandas as pd, numpy as np
import json, zipfile, hashlib, html, re, itertools, math, sys
from collections import defaultdict
from datetime import datetime,timezone
sys.stdout.reconfigure(encoding='utf-8')
from runtime_config import INPUT,OUTPUT,ground_opportunities
P=INPUT;W=INPUT;B=OUTPUT/'bridge'
O=B/'results/cross_source';S=B/'support/cross_source'
SPECIES=['Ardea cinerea','Ciconia ciconia','Fulica atra','Himantopus himantopus','Limosa limosa','Phalacrocorax carbo','Phoenicopterus roseus','Platalea leucorodia','Recurvirostra avosetta']
SECTORS={'PNC':'Parque Nacional De Doñana','SB':'Salinas De Bonanza'}
KEYS=[f'Localidad nivel {i}' for i in range(1,5)]
REG={};MEM=[]
def protect(p):
 p=Path(p).resolve();h=hashlib.sha256(p.read_bytes()).hexdigest(); old=REG.get(str(p));assert old is None or old['sha256']==h
 REG[str(p)]={'path':str(p),'sha256':h,'bytes':p.stat().st_size};return p
def read(p,**kw):return pd.read_csv(protect(p),encoding='utf-8-sig',**kw)
def out(name,d):
 f=O/name;f.resolve().relative_to(B.resolve());pd.DataFrame(d).to_csv(f,index=False,encoding='utf-8-sig')
def rank(a):
 z=sorted(enumerate(a),key=lambda x:x[1]);r=[0.]*len(z);i=0
 while i<len(z):
  j=i+1
  while j<len(z) and z[j][1]==z[i][1]:j+=1
  for ix,_ in z[i:j]:r[ix]=(i+1+j)/2
  i=j
 return r
def rho(a,b):
 a=np.asarray(a,float);b=np.asarray(b,float);ok=np.isfinite(a)&np.isfinite(b);a=a[ok];b=b[ok]
 if len(a)<3 or np.ptp(a)==0 or np.ptp(b)==0:return np.nan
 return float(pd.Series(a).rank().corr(pd.Series(b).rank()))
def pure(a,b):
 a=rank(a);b=rank(b);ma=sum(a)/len(a);mb=sum(b)/len(b);aa=sum((x-ma)**2 for x in a);bb=sum((x-mb)**2 for x in b)
 return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(aa*bb) if aa*bb else np.nan
def jsonout(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n',encoding='utf-8')
protect(B/'code/cross_source/CROSS_SOURCE_PLAN_LOCK.md')
v=read(B/'sources/QUALIFIED_VISITS_COUNTS.csv');slots=read(B/'sources/G2_SLOTS.csv');ops=ground_opportunities(B/'sources/NATIVE_OPPORTUNITY_ELIGIBILITY.csv')
a=read(OUTPUT/'aerial/A1_WIDE_COUNTS.csv');a['date']=pd.to_datetime(a.actual_date);a=a.rename(columns={'parent_id':'sector','unit':'event_id'})
g=v[v.position.isin(slots.position)].merge(ops[['opportunity_uid','Censo',*KEYS,'Se censa','surveyed_qualified','opportunity_source_locators_json']],on='opportunity_uid',validate='one_to_one');g=g[g[KEYS[0]].isin(SECTORS.values())].copy();g['sector']=g[KEYS[0]].map({n:s for s,n in SECTORS.items()});g['date']=pd.to_datetime(g.actual_date)
assert len(slots)==7722 and slots.position.nunique()==702 and not g.opportunity_uid.duplicated().any()
Z=protect(INPUT/'raw_aerial.zip')
with zipfile.ZipFile(Z) as z:
 native={}
 for m in ['aerial/01-aerial_counts.csv','aerial/02-aerial_counts_localities.csv','aerial/03-aerial_counts_data.csv']:
  b=z.read(m);MEM.append({'container':str(Z),'member':m,'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)});native[m]=pd.read_csv(z.open(m),keep_default_na=False)
ac=native['aerial/01-aerial_counts.csv'];ar=native['aerial/02-aerial_counts_localities.csv'];ab=native['aerial/03-aerial_counts_data.csv'];ab['taxon']=ab.Especie.map(lambda x:html.unescape(re.sub('<[^>]+>','',x)).strip())
assert not ac.Censo.duplicated().any();adate=ac.set_index('Censo').Fecha.to_dict();air_checks=[]
for rr in a.to_dict('records'):
 sec=rr['sector'];eid=rr['event_id'];r=ar[(ar.Censo==eid)&(ar[KEYS[0]]==SECTORS[sec])];assert len(r)>0 and r['Se censa'].astype(str).str.lower().eq('true').all();assert adate[eid]==rr['actual_date']
 counts=ab[(ab.Censo==eid)&(ab[KEYS[0]]==SECTORS[sec])].groupby('taxon').Individuos.sum().to_dict()
 for sp in SPECIES:
  value=int(counts.get(sp,0));assert value==rr[sp];air_checks.append({'event_id':eid,'sector':sec,'species':sp,'raw_count':value,'matched':True,'zero_basis':'COMPLETE_LISTED_NATIVE_ROSTER' if value==0 else 'RAW_POSITIVE_ROWS','roster_n':len(r)})
out('AERIAL_ORIGINAL_ROW_RECONCILIATION.csv',air_checks)
# Independently reopen original terrestrial locality and positive files; no positive-row absence can qualify a zero.
raw02={};raw03={};ground_checks=[]
for rr in g.to_dict('records'):
 locators=json.loads(rr['opportunity_source_locators_json']);assert rr['surveyed_qualified'] and rr['Se censa']=='Sí'
 for loc in locators:
  p,ix=loc.rsplit('#data_row=',1)
  if p not in raw02:raw02[p]=read(p,keep_default_na=False)
  r=raw02[p].iloc[int(ix)-1];assert all(str(r[k])==str(rr[k]) for k in ['Censo',*KEYS]);assert r['Fecha']==rr['actual_date'] and r['Se censa']=='Sí'
  pp=str(Path(p).with_name(Path(p).name.replace('02-terrestrial_count_localities_','03-terrestrial_counts_data_')))
  if pp not in raw03:
   t=read(pp,keep_default_na=False);t['taxon']=t.Especie.map(lambda x:html.unescape(re.sub('<[^>]+>','',x)).strip());t['Individuos']=pd.to_numeric(t.Individuos);raw03[pp]=t.groupby(['Censo',*KEYS,'taxon']).Individuos.sum().to_dict()
 counts=raw03[pp]
 for sp in SPECIES:assert int(counts.get(tuple(rr[k] for k in ['Censo',*KEYS])+ (sp,),0))==rr[sp]
 ground_checks.append({'opportunity_uid':rr['opportunity_uid'],'actual_date':rr['actual_date'],'original02_locators':rr['opportunity_source_locators_json'],'nine_responses_raw_matched':True,'qualified_zero_basis':'SOURCE02_SURVEYED_PLUS_FOCAL_REPORTING_CONTRACT'})
out('GROUND_ORIGINAL_ROW_RECONCILIATION.csv',ground_checks)
# Lock stable named nesting using all A1 rosters, independent of outcomes.
members=[];excluded=[];monthkids={}
for (sec,m),zz in g.groupby(['sector','month']):
 ev=a[(a.sector==sec)&(a.month==m)]
 if ev.empty:continue
 sets=[]
 for eid in ev.event_id:
  r=ar[(ar.Censo==eid)&(ar[KEYS[0]]==SECTORS[sec])&ar['Se censa'].astype(str).str.lower().eq('true')];sets.append(set(map(tuple,r[KEYS[:3]].to_numpy())))
 common=set.intersection(*sets);kids=[]
 for cid,t in zz.groupby('child_id'):
  identities=t[KEYS].drop_duplicates();assert len(identities)==1
  nativekey=tuple(identities.iloc[0][KEYS[:3]])
  rec={'sector':sec,'month':int(m),'child_id':cid,'position':t.position.iloc[0],**identities.iloc[0].to_dict(),'n_native_aerial_events':len(ev),'historical_triplet_all_events':nativekey in common,'n_ground_years':t.year.nunique()}
  (members if nativekey in common else excluded).append(rec)
  if nativekey in common:kids.append(cid)
 if kids:monthkids[(sec,int(m))]=set(kids)
out('FIXED_HISTORICALLY_NESTED_CHILD_MONTH_ROSTER.csv',members);out('EXCLUDED_UNRESOLVED_NAMED_POSITIONS.csv',excluded)
# Native ground reference: exactly the same per-calendar-month roster, all 11 years.
gn=[]
for (sec,m),kids in monthkids.items():
 t=g[(g.sector==sec)&(g.month==m)&g.child_id.isin(kids)]
 child=t.groupby(['year','child_id'])[SPECIES].mean().reset_index()
 for yr,tt in child.groupby('year'):
  assert set(tt.child_id)==kids
  rec={'sector':sec,'year':int(yr),'month':m,'n_children':len(kids)};rec.update(tt[SPECIES].mean().to_dict());gn.append(rec)
gn=pd.DataFrame(gn);out('GROUND_NATIVE_FIXED_SUBSET_MONTHLY_SERIES.csv',gn)
base=[]
for source,df in [('AIR',a),('GROUND',gn)]:
 for (sec,m),t in df.groupby(['sector','month']):
  for sp in SPECIES:base.append({'source':source,'sector':sec,'month':int(m),'species':sp,'n_years':t.year.nunique(),'n_observations':len(t),'median_log1p':float(np.median(np.log1p(t[sp]))) if t.year.nunique()>=3 else np.nan,'reference_state':'QUALIFIED' if t.year.nunique()>=3 else 'UNDEFINED_LT3_SAMPLED_YEARS'})
base=pd.DataFrame(base);out('NATIVE_MONTH_REFERENCES.csv',base);bd=base.set_index(['source','sector','month','species']).median_log1p.to_dict()
# Construct eligible edges, unique visit allocation before any species is read for matching.
edges=[];crossmonth=[]
for ai,rr in a.iterrows():
 kids=monthkids.get((rr.sector,int(rr.month)),set())
 for cid in sorted(kids):
  t=g[(g.sector==rr.sector)&(g.child_id==cid)].copy();t['gap']=(t.date-rr.date).dt.days;t=t[t.gap.abs()<=14]
  for gi,gr in t.iterrows():
   rec={'ai':int(ai),'gi':int(gi),'event_id':rr.event_id,'sector':rr.sector,'child_id':cid,'opportunity_uid':gr.opportunity_uid,'aerial_date':rr.actual_date,'ground_date':gr.actual_date,'signed_days':int(gr.gap),'absolute_days':abs(int(gr.gap))}
   if int(gr.month)==int(rr.month):edges.append(rec)
   else:crossmonth.append(rec)
edges=sorted(edges,key=lambda r:(r['absolute_days'],r['ground_date'],r['opportunity_uid'],r['event_id']));used=set();allocated={}
for r in edges:
 key=(r['ai'],r['child_id'])
 if key not in allocated and r['opportunity_uid'] not in used:allocated[key]=r;used.add(r['opportunity_uid'])
out('DISCARDED_ADJACENT_CALENDAR_MONTH_CANDIDATES.csv',crossmonth)
match=[];eventcov=[];pairrows=[];complete={}
for ai,rr in a.iterrows():
 kids=monthkids.get((rr.sector,int(rr.month)),set());alloc=[allocated[(int(ai),cid)] for cid in sorted(kids) if (int(ai),cid) in allocated]
 ok=len(kids)>0 and len(alloc)==len(kids)
 ec={'sector':rr.sector,'event_id':rr.event_id,'aerial_date':rr.actual_date,'year':int(rr.year),'month':int(rr.month),'required_children':len(kids),'matched_children':len(alloc),'complete_14d':ok,'same_day_children':sum(x['absolute_days']==0 for x in alloc),'within7_children':sum(x['absolute_days']<=7 for x in alloc),'ground_date_min':min((x['ground_date'] for x in alloc),default=''),'ground_date_max':max((x['ground_date'] for x in alloc),default=''),'max_abs_days':max((x['absolute_days'] for x in alloc),default=np.nan),'coverage_state':'COMPLETE_FIXED_MONTH_ROSTER' if ok else ('NO_G2_NATIVE_MONTH_ROSTER' if not kids else 'INCOMPLETE_WITHIN_14D_NO_ZERO_FILL')}
 ec['ground_date_span_days']=(pd.Timestamp(ec['ground_date_max'])-pd.Timestamp(ec['ground_date_min'])).days if alloc else np.nan;eventcov.append(ec)
 for x in alloc:match.append({**x,'kept_complete_event':ok,'direction':'SAME_DAY' if x['signed_days']==0 else ('GROUND_BEFORE_AIR' if x['signed_days']<0 else 'GROUND_AFTER_AIR'),'historical_coverage':'EXACT_NATIVE_L3_NESTED_L4_SUBSET;FOOTPRINT_NOT_EQUAL'})
 if not ok:continue
 complete[rr.event_id,rr.sector]=alloc
 tt=g.loc[[x['gi'] for x in alloc]];assert len(tt)==len(kids) and set(tt.child_id)==kids
 for sp in SPECIES:
  gv=float(tt[sp].mean());av=float(rr[sp]);ga=bd.get(('GROUND',rr.sector,int(rr.month),sp),np.nan);aa=bd.get(('AIR',rr.sector,int(rr.month),sp),np.nan)
  pairrows.append({**ec,'species':sp,'ground_mean_per_fixed_child':gv,'aerial_sector_count':av,'ground_native_reference':ga,'air_native_reference':aa,'ground_departure':np.log1p(gv)-ga,'air_departure':np.log1p(av)-aa,'reference_state':'QUALIFIED' if np.isfinite(ga) and np.isfinite(aa) else 'UNDEFINED_NATIVE_REFERENCE','complete_7d':all(x['absolute_days']<=7 for x in alloc),'complete_same_day':all(x['absolute_days']==0 for x in alloc)})
out('ACTUAL_DATE_MATCHED_VISITS.csv',match);out('AERIAL_EVENT_COVERAGE_AND_DROPPED_SUPPORT.csv',eventcov);pairs=pd.DataFrame(pairrows);out('PAIRED_EVENT_SPECIES_VALUES_AND_NATIVE_DEPARTURES.csv',pairs)
assert len({r['opportunity_uid'] for r in match})==len(match)
summary=[];same=[];influence=[];mat=[];checks=[]
for sec in SECTORS:
 t=pairs[pairs.sector==sec]
 for scenario,ss in [('MAIN_14D',t),('WITHIN7D',t[t.complete_7d]),('SAME_DAY',t[t.complete_same_day])]:
  meta=ss.drop_duplicates('event_id');summary.append({'sector':sec,'scenario':scenario,'n_events':len(meta),'n_years':meta.year.nunique(),'months':'|'.join(map(str,sorted(meta.month.unique()))),'n_ground_visits':int(meta.required_children.sum()),'min_children':meta.required_children.min(),'max_children':meta.required_children.max(),'n_before_air':sum(x['signed_days']<0 for k,z in complete.items() if k[1]==sec and k[0] in set(meta.event_id) for x in z),'n_same_day_visits':sum(x['signed_days']==0 for k,z in complete.items() if k[1]==sec and k[0] in set(meta.event_id) for x in z),'n_after_air':sum(x['signed_days']>0 for k,z in complete.items() if k[1]==sec and k[0] in set(meta.event_id) for x in z)})
  for sp in SPECIES:
   z=ss[(ss.species==sp)&ss.reference_state.eq('QUALIFIED')].copy();qualified=z.year.nunique()>=3
   r=rho(z.ground_departure,z.air_departure) if qualified else np.nan
   state='DESCRIPTIVE_ON_QUALIFIED_NATIVE_REFERENCE' if np.isfinite(r) else ('UNDEFINED_LT3_PAIRED_YEARS' if not qualified else 'UNDEFINED_CONSTANT_OR_LT3_POINTS')
   same.append({'sector':sec,'scenario':scenario,'species':sp,'n_events':len(z),'n_years':z.year.nunique(),'rho_departure':r,'rho_raw_native_response':rho(z.ground_mean_per_fixed_child,z.aerial_sector_count) if qualified else np.nan,'state':state})
   if np.isfinite(r):checks.append({'check':'independent_average_rank_pearson','family':'same_species','sector':sec,'scenario':scenario,'species':sp,'absolute_error':abs(r-pure(z.ground_departure.tolist(),z.air_departure.tolist()))})
   if scenario=='MAIN_14D':
    for yr in sorted(z.year.unique()):
     d=z[z.year!=yr];rrho=rho(d.ground_departure,d.air_departure) if d.year.nunique()>=3 else np.nan;influence.append({'sector':sec,'species':sp,'deleted_year':int(yr),'n_events':len(d),'n_years':d.year.nunique(),'rho_departure':rrho,'native_reference':'RETAINED_FULL_NATIVE_REFERENCE'})
  # All pair edges use the same complete nine-species event support.
  good=ss[ss.reference_state.eq('QUALIFIED')].groupby('event_id').species.nunique();ids=good[good==len(SPECIES)].index;sm=ss[ss.event_id.isin(ids)]
  for sens in ['NATIVE_DEPARTURE','WITHIN_YEAR_CENTERED','LINEAR_YEAR_RESIDUAL']:
   vals={}
   for source,col in [('AIR','air_departure'),('GROUND','ground_departure')]:
    vv=sm.pivot(index='event_id',columns='species',values=col);md=sm.drop_duplicates('event_id').set_index('event_id').loc[vv.index,['year','month']]
    if sens=='WITHIN_YEAR_CENTERED':
     yc=md.year.value_counts();vv=vv.loc[md.year.isin(yc[yc>=2].index)];md=md.loc[vv.index];vv=vv-vv.groupby(md.year).transform('mean')
    elif sens=='LINEAR_YEAR_RESIDUAL' and len(vv):
     x=np.column_stack([np.ones(len(vv)),md.year.to_numpy()-md.year.mean()]);vv=pd.DataFrame(vv.to_numpy()-x@np.linalg.lstsq(x,vv.to_numpy(),rcond=None)[0],index=vv.index,columns=vv.columns)
    vals[source]=(vv,md)
   for sp1,sp2 in itertools.combinations(SPECIES,2):
    row={'sector':sec,'scenario':scenario,'adjustment':sens,'species_a':sp1,'species_b':sp2}
    for source in ['AIR','GROUND']:
     vv,md=vals[source];r=rho(vv[sp1],vv[sp2]) if md.year.nunique()>=3 else np.nan;row[source.lower()+'_rho']=r;row['n_events']=len(vv);row['n_years']=md.year.nunique()
     if np.isfinite(r):checks.append({'check':'independent_average_rank_pearson','family':'pair_structure','sector':sec,'scenario':scenario,'adjustment':sens,'source':source,'species':sp1+';'+sp2,'absolute_error':abs(r-pure(vv[sp1].tolist(),vv[sp2].tolist()))})
    arho=row['air_rho'];grho=row['ground_rho'];row['direction_state']='UNDEFINED' if not np.isfinite(arho*grho) else ('SAME_SIGN' if arho*grho>0 else ('OPPOSITE_SIGN' if arho*grho<0 else 'ZERO_EDGE'))
    mat.append(row)
# Alternative matched references: medians change only on the paired support and keep >=3 sampled years.
alt=[]
for (sec,sp,m),z in pairs.groupby(['sector','species','month']):
 yy=z.year.nunique();dd=z.copy()
 for src,col in [('air','aerial_sector_count'),('ground','ground_mean_per_fixed_child')]:dd[src+'_matched_departure']=np.log1p(dd[col])-np.median(np.log1p(dd[col])) if yy>=3 else np.nan
 dd['matched_reference_n_years']=yy;alt.append(dd)
alt=pd.concat(alt,ignore_index=True)
out('MATCHED_SUPPORT_REFERENCE_DEPARTURES.csv',alt)
altrows=[]
for (sec,sp),z in alt.groupby(['sector','species']):
 d=z.dropna(subset=['air_matched_departure','ground_matched_departure']);r=rho(d.air_matched_departure,d.ground_matched_departure) if d.year.nunique()>=3 else np.nan;altrows.append({'sector':sec,'species':sp,'n_events':len(d),'n_years':d.year.nunique(),'rho_departure':r,'reference':'MATCHED_SUPPORT_MEDIAN_LOG1P_GE3_YEARS'})
out('MATCHED_REFERENCE_SENSITIVITY.csv',altrows);out('MATCHED_SUPPORT_SUMMARY.csv',summary);out('SAME_SPECIES_TEMPORAL_CORRESPONDENCE.csv',same);out('LEAVE_ONE_YEAR_OUT_CORRESPONDENCE.csv',influence);out('SAME_EVENT_SPECIES_PAIR_STRUCTURE.csv',mat);out('INDEPENDENT_RANK_ARITHMETIC_CHECKS.csv',checks)
assert max((r['absolute_error'] for r in checks),default=0)<1e-12
out('SOURCE_READ_HASH_REGISTER.csv',REG.values());out('ZIP_MEMBER_IDENTITIES.csv',MEM)
unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==r['sha256'] for p,r in REG.items());assert unchanged
state={'status':'ACTUAL_DATE_MATCHING_AND_TEMPORAL_ANALYSES_EXECUTED','current_aerial':'A1_PNC75_SB113','G2_source_slots':len(slots),'native_ground_sector_visits_verified':len(g),'historically_nested_positions':len(members),'excluded_positions':len(excluded),'candidate_adjacent_month_edges_discarded':len(crossmonth),'matched_events_14d':int(pairs[['sector','event_id']].drop_duplicates().shape[0]),'source_hashes_unchanged':unchanged,'independent_rank_checks':len(checks),'maximum_rank_error':max((r['absolute_error'] for r in checks),default=0),'same_day_sparse_scope':'See MATCHED_SUPPORT_SUMMARY.csv','claim_ceiling':'Descriptive finite-support correspondence of methods on native nested partial named ground subset; not calibration, population abundance, footprint equality or individual movement','created_utc':datetime.now(timezone.utc).isoformat()}
jsonout(O/'MODULE_STATE.json',state)
print(json.dumps(state,ensure_ascii=False,indent=2));print(pd.DataFrame(summary).to_string(index=False));print(pd.DataFrame(same).query('scenario=="MAIN_14D"').to_string(index=False));print(pd.DataFrame(mat).query('scenario=="MAIN_14D"').groupby(['sector','adjustment','direction_state']).size().to_string())
