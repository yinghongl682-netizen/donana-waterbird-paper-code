from bridge_common import *
import zipfile
from fractions import Fraction as F
assert sha(OR2)=='423b4ea7c046d1cc8b3b1b7089cb1b2eb5bf4bb362e58265a619aee6b02af9ee'
f=load();z=zipfile.ZipFile(OR2);checks=[]
def check(scope,key,field,a,b):
 if pd.isna(a) or pd.isna(b):ok=pd.isna(a) and pd.isna(b);err=0 if ok else np.inf
 else:err=abs(float(a)-float(b));ok=err<=1e-10+1e-12*abs(float(b))
 checks.append(dict(scope=scope,key=key,field=field,recomputed=a,reference=b,absolute_error=err,pass_check=ok))
components=pd.read_csv(z.open('Table_S6_Ground_Components.csv'));components=components[components.configuration=='G2']
alias={'MAM':'MarMay','JJA':'JunJul','Mar/May':'MarMay','Jun/Jul':'JunJul'}
fields={'frequency_early':'early_f','mean_count_early':'early_mu','positive_mean_early':'early_q','frequency_late':'late_f','mean_count_late':'late_mu','positive_mean_late':'late_q','delta_mean_count':'delta_mu','frequency_arithmetic_contribution':'Cf','positive_count_arithmetic_contribution':'Cq','n_cells_early':'early_n','n_cells_late':'late_n','positive_cells_early':'early_positive_n','positive_cells_late':'late_positive_n'}
rows=[]
for _,r in components.iterrows():
 win=alias.get(r.window,r.window);x=f[f.month.isin(WINDOWS[win])];e=stat(x.loc[x.year<=2017,r.species]);l=stat(x.loc[x.year>=2018,r.species]);c=contrast(e,l)
 out=dict(species=r.species,window=win,**{'early_'+k:v for k,v in e.items()},**{'late_'+k:v for k,v in l.items()},**c);rows.append(out)
 for a,b in fields.items():check('period',r.species+'|'+win,a,out[b],r[a])
 # Exact independent arithmetic on integer totals and positive counts.
 fe=F(e['positive_n'],e['n']);fl=F(l['positive_n'],l['n']);me=F(int(e['recorded_sum']),e['n']);ml=F(int(l['recorded_sum']),l['n'])
 qe=F(int(e['recorded_sum']),e['positive_n']) if e['positive_n'] else None;ql=F(int(l['recorded_sum']),l['positive_n']) if l['positive_n'] else None
 exact={'exact_early_frequency':fe,'exact_late_frequency':fl,'exact_early_mean_count':me,'exact_late_mean_count':ml,'exact_delta_mean_count':ml-me,'exact_early_positive_mean':qe,'exact_late_positive_mean':ql,'exact_delta_frequency':fl-fe,'exact_delta_positive_mean':ql-qe if qe is not None and ql is not None else None,'exact_Cf':(fl-fe)*(ql+qe)/2 if qe is not None and ql is not None else None,'exact_Cq':(ql-qe)*(fl+fe)/2 if qe is not None and ql is not None else None}
 for k,v in exact.items():
  ref=None if pd.isna(r[k]) or str(r[k]) in ('UNDEFINED','None','') else F(str(r[k]))
  checks.append(dict(scope='exact_period',key=r.species+'|'+win,field=k,recomputed=str(v),reference=str(ref),absolute_error=0 if v==ref else np.inf,pass_check=v==ref))
annual=pd.read_csv(z.open('Ground_Annual_2013_2023.csv'));annual=annual[annual.configuration=='G2']
for _,r in annual.iterrows():
 x=f[f.year==r.year];st=stat(x[r.species]);ch,pa,su=concentration(x,r.species)
 for field,k in [('frequency','f'),('mean_count','mu'),('positive_mean','q'),('positive_cells','positive_n'),('n_cells','n')]:check('annual',r.species+'|'+str(r.year),field,st[k],r[field])
 for field,k in [('child_hhi','HHI_child'),('parent_hhi','HHI_parent')]:check('annual',r.species+'|'+str(r.year),field,su[k],r[field])
ep=pd.read_csv(z.open('Parent_Endpoint_Contributions.csv'));ep=ep[ep.configuration=='G2']
for sp in ['Fulica atra','Netta rufina']:
 for year in [2013,2023]:
  _,pa,_=concentration(f[f.year==year],sp)
  for _,p in pa.iterrows():
   r=ep[(ep.species==sp)&(ep.parent_code==p.parent_code)].iloc[0]
   for a,b in [('Y','Y'),('W','W'),('H','Hwithin'),('K','child_HHI_contribution')]:check('parent_endpoint',sp+'|'+p.parent_code+'|'+str(year),a,p[a],r[b+'_'+str(year)])
save('support/BASELINE_COMPARISONS.csv',checks);save('results/ground/BASELINE_PERIOD_COMPONENTS.csv',rows)
native=pd.read_csv(ROOT/'sources/G2_SLOTS.csv');stored=pd.read_csv(INPUT/'oracles/G2_SLOTS.csv')
assert native.sort_values(['year','position']).reset_index(drop=True)[['year','position']+SPECIES].equals(stored.sort_values(['year','position']).reset_index(drop=True)[['year','position']+SPECIES])
summary=dict(status='PASS' if all(r['pass_check'] for r in checks) else 'FAIL',comparisons=len(checks),max_absolute_error=max(r['absolute_error'] for r in checks),absolute_tolerance=1e-10,relative_tolerance=1e-12,exact_fraction_rows=sum(r['scope']=='exact_period' for r in checks),OR2_sha256=sha(OR2),slots=len(f),positions=f.position.nunique(),children=f.child_id.nunique(),parents=f.parent_id.nunique(),fresh_raw_values_equal_archived_G2=True,run_utc=now())
jout('support/BASELINE_GATE.json',summary);print(json.dumps(summary));assert summary['status']=='PASS'
