from pathlib import Path
from fractions import Fraction
import hashlib, json, datetime, sys
import pandas as pd
import numpy as np
sys.dont_write_bytecode=True
from runtime_config import INPUT,OUTPUT
ROOT=OUTPUT/"bridge"
WORK=INPUT
PROJECT=INPUT
WINDOWS={'ANNUAL':[1,2,3,5,6,7,9,10,11,12],'DJF':[12,1,2],'MarMay':[3,5],'JunJul':[6,7],'SON':[9,10,11]}
SPECIES=sorted(['Ardea cinerea','Ciconia ciconia','Fulica atra','Himantopus himantopus','Limosa limosa','Phalacrocorax carbo','Phoenicopterus roseus','Platalea leucorodia','Recurvirostra avosetta','Netta rufina','Aythya ferina','Tadorna tadorna','Anas platyrhynchos'])
OR2=INPUT/'oracles/ground_baseline_OR2.zip'
STAGE6D=INPUT
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def jout(p,x):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2,default=lambda x:x.item() if hasattr(x,'item') else str(x))+'\n',encoding='utf-8')
def save(p,x):
 p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True)
 (x if isinstance(x,pd.DataFrame) else pd.DataFrame(x)).to_csv(p,index=False,encoding='utf-8-sig',float_format='%.17g')
def load(config='G2'):
 f=pd.read_csv(ROOT/f'sources/{config}_SLOTS.csv');f['slot_id']=f.year.astype(str)+'|'+f.position
 assert not f.slot_id.duplicated().any()
 names=pd.read_csv(INPUT/'contracts/parent_display_key.csv')
 f=f.merge(names.rename(columns={'display_name':'parent_name','key':'parent_code'}),on='parent_id',validate='many_to_one')
 a=pd.read_csv(ROOT/'sources/NATIVE_OPPORTUNITY_ELIGIBILITY.csv')
 cn=a.drop_duplicates('child_id').set_index('child_id').locality_name
 f['child_name']=f.child_id.map(cn)
 assert f[SPECIES].notna().all().all()
 assert np.all(f[SPECIES].to_numpy()==np.floor(f[SPECIES].to_numpy()))
 assert f.position.nunique()=={'G2':702,'G3':699}[config]
 return f
def stat(v):
 v=np.asarray(v,float);p=v[v>0];n=len(v)
 return dict(n=n,positive_n=len(p),zero_n=n-len(p),f=len(p)/n,q=float(p.mean()) if len(p) else np.nan,mu=float(v.mean()),recorded_sum=float(v.sum()))
def contrast(e,l):
 defined=np.isfinite(e['q']) and np.isfinite(l['q'])
 cf=(l['f']-e['f'])*(e['q']+l['q'])/2 if defined else np.nan
 cq=(l['q']-e['q'])*(e['f']+l['f'])/2 if defined else np.nan
 return dict(delta_mu=l['mu']-e['mu'],Cf=cf,Cq=cq,q_state='BOTH_PERIODS_POSITIVE' if defined else 'ONE_PERIOD_POSITIVE' if e['positive_n']+l['positive_n']>0 else 'BOTH_ZERO')
def concentration(x,sp):
 ch=x.groupby(['parent_id','parent_name','parent_code','child_id','child_name'],sort=True)[sp].sum().rename('Y').reset_index()
 pa=ch.groupby(['parent_id','parent_name','parent_code'],sort=True).Y.sum().reset_index();T=pa.Y.sum()
 ch=ch.merge(pa[['parent_id','Y']].rename(columns={'Y':'parent_Y'}),on='parent_id',validate='many_to_one')
 ch['global_share']=ch.Y/T if T>0 else np.nan
 ch['within_parent_share']=ch.Y/ch.parent_Y.replace(0,np.nan)
 h=ch.assign(v=ch.within_parent_share**2).groupby('parent_id').v.sum(min_count=1)
 pa['W']=pa.Y/T if T>0 else np.nan;pa['H']=pa.parent_id.map(h)
 pa['K']=np.where(pa.Y>0,pa.W**2*pa.H,0.) if T>0 else np.nan
 pa['H_state']=np.where(pa.Y>0,'DEFINED','UNDEFINED_ZERO_PARENT_TOTAL')
 su=dict(T=T,HHI_parent=float((pa.W**2).sum()) if T>0 else np.nan,HHI_child=float((ch.global_share**2).sum()) if T>0 else np.nan,positive_parents=int((pa.Y>0).sum()),positive_children=int((ch.Y>0).sum()),concentration_state='DEFINED' if T>0 else 'UNDEFINED_ZERO_WINDOW_TOTAL')
 return ch,pa,su
