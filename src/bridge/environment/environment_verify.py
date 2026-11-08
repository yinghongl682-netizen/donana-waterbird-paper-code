from pathlib import Path
import pandas as pd,numpy as np,csv,json,hashlib,datetime
from runtime_config import INPUT,OUTPUT
ROOT=INPUT
B=OUTPUT/'bridge';O=B/'results/environment';S=B/'support/environment'
manifest=[]
def rd(p):
 p=Path(p);manifest.append({'path':str(p),'sha256_before':hashlib.sha256(p.read_bytes()).hexdigest()});return pd.read_csv(p,encoding='utf-8-sig')
d=rd(O/'ENVIRONMENT_NATIVE_ANALYSIS_VISITS.csv');a=rd(O/'FIELD_WATER_FE_COEFFICIENTS.csv');std=rd(O/'COMMON_WATER_STANDARDIZED_PERIOD_RESULTS.csv')
# Independent direct dummy-variable normal-equation implementation, no demeaning helper.
checks=[]
for sp in ['Fulica atra','Netta rufina']:
 for response in ['recorded_positive','positive_log_count']:
  f=d[d.known_water].copy()
  if response=='positive_log_count':f=f[f[sp]>0]
  p=pd.get_dummies(f.position,dtype=float);y=pd.get_dummies(f.year,dtype=float).iloc[:,1:];wc=pd.get_dummies(f.water_code,dtype=float).reindex(columns=list(range(1,6)),fill_value=0)
  X=np.column_stack([p,y,wc]);v=(f[sp]>0).to_numpy(dtype=float) if response=='recorded_positive' else np.log(f[sp].to_numpy())
  beta=np.linalg.solve(X.T@X,X.T@v)[-5:]
  for c,estimate in enumerate(beta,1):
   main=float(a[(a.species==sp)&(a.response==response)&(a.category==c)].estimate.iloc[0]);err=abs(estimate-main);checks.append({'check':'INDEPENDENT_FULL_DUMMY_NORMAL_EQUATIONS','species':sp,'response':response,'category':c,'independent':estimate,'main':main,'absolute_error':err,'pass':err<1e-8})
# Literal native source rows reopened for all G2 water/date records.
cache={};witness=[]
for r in d.to_dict('records'):
 locs=json.loads(r['source_02_locators']);vals=[]
 for locator in locs:
  path,num=locator.rsplit('#data_row=',1);p=Path(path)
  if path not in cache:
   manifest.append({'path':path,'sha256_before':hashlib.sha256(p.read_bytes()).hexdigest()})
   with p.open(encoding='utf-8-sig',newline='') as fh:cache[path]=list(csv.DictReader(fh))
  raw=cache[path][int(num)-1];vals.append(raw['Nivel de agua'])
 assert all(v==r['water_literal'] for v in vals),(r['opportunity_uid'],vals,r['water_literal'])
 witness.append({'opportunity_uid':r['opportunity_uid'],'water_literal':r['water_literal'],'water_code':r['water_code'],'original_rows':len(locs),'all_original_literals_match':True,'locators':r['source_02_locators']})
pd.DataFrame(witness).to_csv(S/'ORIGINAL_WATER_ROW_RECHECK.csv',index=False,encoding='utf-8-sig')

# Independent common-water standardization by csv/Python loops for all13; no pandas group aggregation reuse.
with (O/'COMMON_WATER_STRATUM_RESULTS.csv').open(encoding='utf-8-sig',newline='') as fh:rows=list(csv.DictReader(fh))
from collections import defaultdict
tot=defaultdict(lambda:[0.,0.,set()])
for r in rows:
 for metric in ['f','mu']:
  k=(r['species'],metric);tot[k][0]+=float(r['within_position_weight'])*float(r[metric+'_E']);tot[k][1]+=float(r['within_position_weight'])*float(r[metric+'_L']);tot[k][2].add(r['position'])
for (sp,metric),(e,l,ps) in tot.items():
 val=(l-e)/len(ps);main=float(std[(std.species==sp)&(std.metric==metric)].standardized_delta.iloc[0]);err=abs(val-main)
 checks.append({'check':'INDEPENDENT_CSV_STANDARDIZATION','species':sp,'response':metric,'category':None,'independent':val,'main':main,'absolute_error':err,'pass':err<1e-9})
pd.DataFrame(checks).to_csv(S/'INDEPENDENT_ENVIRONMENT_ARITHMETIC.csv',index=False,encoding='utf-8-sig')
assert all(r['pass'] for r in checks)

# Actual environment-native data coverage; no new effect selection from this inventory.
env=rd(INPUT/'oracles/environment_observation_coverage.csv')
fam=env.groupby(['source_family','spatial_domain','source_support_state'],dropna=False).agg(rows=('observation_id','size'),first_date=('date','min'),last_date=('date','max'),distinct_dates=('date','nunique')).reset_index()
fam.to_csv(O/'EXISTING_ENVIRONMENT_OBSERVATION_COVERAGE.csv',index=False,encoding='utf-8-sig')
station=rd(INPUT/'oracles/station_date_support.csv')
st=station.drop_duplicates(['station_id','instrument','date']);stg=st.groupby(['station_id','instrument']).agg(rows=('date','size'),first_date=('date','min'),last_date=('date','max'),numeric=('value_m','count')).reset_index();stg['overlap_2013_2023_days']=0
assert st.date.min()>'2023-12-31'
stg.to_csv(O/'LOCAL_STATION_DATE_SUPPORT.csv',index=False,encoding='utf-8-sig')
chem=rd(INPUT/'oracles/chemistry_date_support.csv')
chem.to_csv(O/'CHEMISTRY_EXISTING_DATE_SUPPORT.csv',index=False,encoding='utf-8-sig')
gate=rd(INPUT/'oracles/existing_exposure_gate.csv')
gate.to_csv(O/'EXISTING_BIRD_RS_EXPOSURE_GATE.csv',index=False,encoding='utf-8-sig');assert not gate.qualified.any()
for r in manifest:r['sha256_after']=hashlib.sha256(Path(r['path']).read_bytes()).hexdigest();r['unchanged']=r['sha256_before']==r['sha256_after']
assert all(r['unchanged'] for r in manifest)
pd.DataFrame(manifest).drop_duplicates('path').to_csv(S/'ACTUAL_ENVIRONMENT_SOURCE_HASHES.csv',index=False,encoding='utf-8-sig')
(S/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'coefficient_checks':20,'standardization_checks':26,'max_absolute_error':max(r['absolute_error'] for r in checks),'all_pass':True,'native_water_rows_reopened':len(witness),'raw_source_files':len(cache),'hydromet_rows':len(station),'unique_station_instrument_days':len(st),'station_date_min':st.date.min(),'station_date_max':st.date.max(),'rs_gates':len(gate),'rs_gates_qualified':int(gate.qualified.sum()),'protected_sources_unchanged':True},ensure_ascii=False,indent=2),encoding='utf-8')
print('Independent checks passed',len(checks),'raw water rows',len(witness),'max error',max(r['absolute_error'] for r in checks))
