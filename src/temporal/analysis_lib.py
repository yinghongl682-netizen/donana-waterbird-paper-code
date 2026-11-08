from common import *
import pandas as pd,numpy as np,math,itertools,collections
from fractions import Fraction as F
AIRSPEC=['Ardea cinerea','Ciconia ciconia','Fulica atra','Himantopus himantopus','Limosa limosa','Phalacrocorax carbo','Phoenicopterus roseus','Platalea leucorodia','Recurvirostra avosetta']
FOCAL=['Fulica atra','Netta rufina']
YEARS=list(range(2013,2024));WINDOWS={'ANNUAL':list(range(1,13)),'DJF':[1,2,12],'MAM':[3,5],'JJA':[6,7],'SON':[9,10,11]}
def df(p):return pd.read_csv(protect(p),encoding='utf-8-sig')
def finite(v):
 try:return v is not None and str(v)!='' and math.isfinite(float(v))
 except (TypeError,ValueError):return False
def number(v):return float(v) if v is not None else None
def sign(v):return 'UNDEFINED' if not finite(v) else 'POSITIVE' if v>0 else 'NEGATIVE' if v<0 else 'ZERO'
def rank(v):
 indexed=sorted(enumerate(v),key=lambda x:x[1]);r=[0.0]*len(v);i=0
 while i<len(v):
  j=i+1
  while j<len(v) and indexed[j][1]==indexed[i][1]:j+=1
  for k,_ in indexed[i:j]:r[k]=(i+1+j)/2
  i=j
 return r
def rho(a,b):
 a=np.asarray(a,float);b=np.asarray(b,float);valid=np.isfinite(a)&np.isfinite(b);a=a[valid];b=b[valid]
 if len(a)<3 or len(set(a))<2 or len(set(b))<2:return None
 return float(np.corrcoef(rank(a),rank(b))[0,1])
def air_load():
 a=df(C/'A1_WIDE_COUNTS.csv');assert len(a)==188 and not a.duplicated(['unit','parent_id']).any()
 assert a.groupby('parent_id').size().to_dict()=={'PNC':75,'SB':113}
 assert list(a.columns[5:])==AIRSPEC
 dt=pd.to_datetime(a.actual_date);assert (dt.dt.year==a.year).all() and (dt.dt.month==a.month).all()
 assert np.isfinite(a[AIRSPEC].values).all() and (a[AIRSPEC].values>=0).all()
 return a
def air_departures(a,threshold=3):
 long=a.melt(id_vars=['unit','parent_id','actual_date','year','month'],value_vars=AIRSPEC,var_name='species',value_name='y');long['L']=np.log1p(long.y)
 b=long.groupby(['parent_id','species','month']).agg(n_years=('year','nunique'),n_events=('unit','size'),median_log1p=('L','median')).reset_index()
 b['reportable']=b.n_years>=threshold;b.loc[~b.reportable,'median_log1p']=np.nan
 z=long.merge(b[['parent_id','species','month','median_log1p']],on=['parent_id','species','month'],validate='many_to_one');z['departure']=z.L-z.median_log1p
 return z,b
def air_pivots(z,value='departure'):
 return {sec:z[(z.parent_id==sec)&z[value].notna()].pivot(index='unit',columns='species',values=value).sort_index() for sec in ['PNC','SB']}
def air_pair_rows(z,value='departure'):
 piv=air_pivots(z,value);shared=set(piv['PNC'].index)&set(piv['SB'].index);rows=[]
 for sec in ['PNC','SB']:
  for scenario,ids in [('NATIVE_SUPPORT',set(piv[sec].index)),('COMMON_EVENTS_NATIVE_BASELINE_RETAINED',shared)]:
   d=piv[sec].loc[sorted(ids)]
   for s,t in itertools.combinations(AIRSPEC,2):rows.append(dict(sector=sec,scenario=scenario,species_a=s,species_b=t,n_paired_events=len(d[[s,t]].dropna()),rho=rho(d[s],d[t])))
 return rows
def ground_load(g='G2'):
 f=df(D/f'sources/{g}_SLOTS.csv');n=702 if g=='G2' else 699
 assert len(f)==n*11 and f.position.nunique()==n and not f.duplicated(['year','position']).any()
 assert sorted(f.year.unique())==YEARS and f.groupby('year').size().eq(n).all()
 assert all(set(v.position)==set(f.position) for _,v in f.groupby('year'))
 assert f.child_id.nunique()==90 and f.parent_id.nunique()==30 and f.groupby('child_id').parent_id.nunique().eq(1).all()
 species=[s for s in f.columns if s in AIRSPEC+['Netta rufina','Aythya ferina','Tadorna tadorna','Anas platyrhynchos']];assert len(species)==13 and set(AIRSPEC).issubset(species)
 v=f[species].to_numpy(float);assert np.isfinite(v).all() and (v>=0).all();assert np.array_equal(v,np.floor(v)),'Current frozen one-visit slots must retain integer-valued observations; no rounding allowed'
 for s in species:f[s]=f[s].astype('int64')
 return f,species
def stats(v):
 values=[int(x) for x in v];n=len(values);assert n>0
 p=[x for x in values if x>0];total=sum(values)
 return dict(n_slots=n,n_positive=len(p),recorded_sum=total,f=F(len(p),n),mu=F(total,n),q=F(total,len(p)) if p else None)
def contrast(e,l):
 dq=l['q']-e['q'] if e['q'] is not None and l['q'] is not None else None
 cf=(l['f']-e['f'])*(l['q']+e['q'])/2 if dq is not None else None
 cq=dq*(l['f']+e['f'])/2 if dq is not None else None
 dm=l['mu']-e['mu']
 if cf is not None:assert dm==cf+cq
 return dict(delta_mu=dm,delta_f=l['f']-e['f'],delta_q=dq,Cf=cf,Cq=cq,dominant_component='UNDEFINED' if cf is None else 'FREQUENCY' if abs(cf)>abs(cq) else 'CONDITIONAL_COUNT' if abs(cq)>abs(cf) else 'TIE')
def hierarchy(f,s,year):
 zz=f[f.year==year];child={str(c):int(v) for c,v in zz.groupby('child_id')[s].sum().items()};cp=zz.drop_duplicates('child_id').set_index('child_id').parent_id.astype(str).to_dict()
 parent={str(p):int(v) for p,v in zz.groupby('parent_id')[s].sum().items()};total=sum(child.values());assert total==sum(parent.values()) and total>0
 W={p:F(y,total) for p,y in parent.items()};H={p:sum((F(child[c],y)**2 for c in child if cp[c]==p),F()) if y>0 else None for p,y in parent.items()};K={p:W[p]**2*H[p] if H[p] is not None else F(0) for p in parent}
 hc=sum((F(v,total)**2 for v in child.values()),F());hp=sum((v**2 for v in W.values()),F());assert sum(K.values(),F())==hc
 return dict(child=child,parent=parent,cp=cp,total=total,W=W,H=H,K=K,child_hhi=hc,parent_hhi=hp)
def decompose(e,l,p):
 delta=l['K'][p]-e['K'][p];he=e['H'][p];hl=l['H'][p]
 if he is None or hl is None:return dict(delta_K=delta,between=None,within=None,entry_exit=delta,state='BOTH_ZERO' if he is None and hl is None else 'ENTRY' if he is None else 'EXIT')
 b=(l['W'][p]**2-e['W'][p]**2)*(hl+he)/2;i=(l['W'][p]**2+e['W'][p]**2)*(hl-he)/2;assert delta==b+i
 return dict(delta_K=delta,between=b,within=i,entry_exit=F(0),state='BOTH_POSITIVE')
def numeric_record(st,prefix=''):
 return {prefix+k:number(v) if isinstance(v,F) or v is None else v for k,v in st.items()}
def exact_record(st,prefix=''):
 return {prefix+'exact_'+k:'UNDEFINED' if v is None else str(v) for k,v in st.items() if isinstance(v,F) or v is None}
