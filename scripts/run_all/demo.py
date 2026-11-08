"""SYNTHETIC — NOT ORIGINAL DONANA OBSERVATIONS. Normalized-slot helper demo."""
from pathlib import Path
import argparse,csv,json,os,sys
R=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve()
if out.exists():p.error('Use a new output directory')
out.mkdir(parents=True)
os.environ['DONANA_INPUT_ROOT']=str(R/'data/synthetic_examples');os.environ['DONANA_OUTPUT_ROOT']=str(out)
sys.path[:0]=[str(R/'src'),str(R/'src/bridge')]
from bridge_common import stat,contrast,concentration
import pandas as pd,numpy as np
f=pd.read_csv(R/'data/synthetic_examples/normalized_ground_slots.csv')
assert f.data_role.eq('SYNTHETIC — NOT ORIGINAL DONANA OBSERVATIONS').all()
assert not f.duplicated(['year','position']).any()
species=['Example alpha','Example beta','Example zero'];summary=[];parents=[];indices=[]
for sp in species:
 assert np.isfinite(f[sp]).all() and (f[sp]>=0).all()
 e=stat(f.loc[f.year<=2017,sp]);l=stat(f.loc[f.year>=2018,sp]);c=contrast(e,l)
 summary.append(dict(data_role='SYNTHETIC — NOT ORIGINAL DONANA OBSERVATIONS',species=sp,**{'early_'+k:v for k,v in e.items()},**{'late_'+k:v for k,v in l.items()},**c))
 for period,mask in [('E',f.year<=2017),('L',f.year>=2018)]:
  z=f[mask].groupby(['position','parent_id','parent_name','parent_code','child_id','child_name'],sort=True)[sp].mean().reset_index()
  ch,pa,su=concentration(z,sp);parents.append(pa.assign(species=sp,period=period));indices.append(dict(species=sp,period=period,**su))
pd.DataFrame(summary).to_csv(out/'synthetic_components.csv',index=False)
pd.concat(parents).to_csv(out/'synthetic_parent_shares.csv',index=False)
pd.DataFrame(indices).to_csv(out/'synthetic_concentration.csv',index=False)
(out/'DEMO_STATE.json').write_text(json.dumps(dict(status='SYNTHETIC_PIPELINE_VERIFIED_ONLY',data_role='SYNTHETIC — NOT ORIGINAL DONANA OBSERVATIONS',scope='Normalized-slot import → preserved summary/decomposition/concentration helpers → CSV output; not raw-source or paper-result reproduction',rows=len(f),species=len(species)),indent=2)+'\n',encoding='utf-8')
print('Synthetic normalized-slot demonstration completed; no research-result claim')
