from pathlib import Path
import pandas as pd, numpy as np, json, hashlib, datetime, sys
sys.dont_write_bytecode=True
from runtime_config import INPUT,OUTPUT
ROOT=INPUT
BASE=OUTPUT/'bridge'
OUT=BASE/'results/environment'; SUP=BASE/'support/environment'
OUT.mkdir(parents=True,exist_ok=True);SUP.mkdir(parents=True,exist_ok=True)
SOURCES=[]
def read(p):
 p=Path(p); SOURCES.append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}); return pd.read_csv(p,encoding='utf-8-sig')
def save(df,name): df.to_csv(OUT/name,index=False,encoding='utf-8-sig',float_format='%.15g')
slots=read(BASE/'sources/G2_SLOTS.csv')
ops=read(BASE/'sources/NATIVE_OPPORTUNITY_ELIGIBILITY.csv')
visits=read(BASE/'sources/QUALIFIED_VISITS_COUNTS.csv')
taxa=[s for s in slots.columns if ' ' in s]
assert len(taxa)==13 and len(slots)==7722
ids=set(v for vs in slots.visit_ids for v in json.loads(vs))
o=ops[ops.opportunity_uid.isin(ids)].copy()
assert len(o)==len(ids) and o.opportunity_uid.is_unique and o.bird_eligible.all()
d=o.merge(visits[['opportunity_uid']+taxa],on='opportunity_uid',validate='one_to_one')
assert len(d)==len(ids)
d['period']=np.where(d.year<=2017,'E','L')
d['known_water']=d.water_code.isin(range(6))
dictionary=read(INPUT/'contracts/ground_variable_dictionary.csv')
codebook=dictionary[dictionary.Variable.eq('Nivel de agua')].to_dict('records')
assert 'Desconocido(6)' in codebook[0]['Descripción']
coverage=d.groupby(['period','water_code','water_state'],dropna=False).agg(visits=('opportunity_uid','size'),positions=('position','nunique'),children=('child_id','nunique'),parents=('parent_id','nunique'),years=('year','nunique'),dates=('actual_date','nunique')).reset_index()
save(coverage,'FIELD_WATER_SUPPORT.csv')
save(d[['opportunity_uid','position','child_id','parent_id','census_id','actual_date','year','month','period','water_code','water_literal','known_water','source_02_locators','field_start','field_end','visibility']+taxa],'ENVIRONMENT_NATIVE_ANALYSIS_VISITS.csv')
pos=d.groupby('position').agg(visits=('opportunity_uid','size'),known=('known_water','sum'),categories=('water_code',lambda v:v[v.isin(range(6))].nunique()),years=('year','nunique')).reset_index()
save(pos,'POSITION_WATER_REPEAT_SUPPORT.csv')
audit={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'SUPPORT_ONLY_BEFORE_NEW_EFFECT_ESTIMATION','native_visits':len(d),'slots':len(slots),'max_slot_visits':int(slots.visit_n.max()),'known_water_visits':int(d.known_water.sum()),'unknown_water_visits':int((~d.known_water).sum()),'varying_water_positions':int((pos.categories>1).sum()),'g2_positions':len(pos),'codebook':codebook,'start_nonmissing':int(d.field_start.notna().sum()),'end_nonmissing':int(d.field_end.notna().sum()),'source_hashes':SOURCES}
(SUP/'SUPPORT_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k not in ['source_hashes','codebook']},ensure_ascii=False))
if '--estimate' not in sys.argv: sys.exit(0)
assert (BASE/'code/environment/ENVIRONMENT_PLAN_LOCK.md').exists()
known=d[d.known_water].copy()
# Equal visit weight equals equal slot weight only after the actual multiplicity check.
assert slots.visit_n.eq(1).all(), 'Multiple-visit slots require a prospectively specified weighting amendment.'

def residualize(A,groups,tol=1e-12):
 out=np.array(A,dtype=float,copy=True)
 for it in range(1000):
  before=out.copy()
  for g in groups:
   codes=pd.factorize(g,sort=True)[0]; n=np.bincount(codes)
   sums=np.zeros((len(n),out.shape[1]));np.add.at(sums,codes,out)
   out-=sums[codes]/n[codes,None]
  err=float(np.max(np.abs(out-before)))
  if err<tol:return out,it+1,err
 raise RuntimeError('Alternating projection did not converge; no optimizer switching.')

def fit_frame(frame,sp,response,dropyear=None):
 f=frame if dropyear is None else frame[frame.year.ne(dropyear)]
 if response=='positive_log_count':f=f[f[sp]>0]
 y=(f[sp].to_numpy()>0).astype(float) if response=='recorded_positive' else np.log(f[sp].to_numpy())
 X=np.column_stack([(f.water_code.to_numpy()==c).astype(float) for c in range(1,6)])
 z,it,err=residualize(np.column_stack([y,X]),[f.position,f.year])
 yy,xx=z[:,0],z[:,1:]
 rank=int(np.linalg.matrix_rank(xx));sv=np.linalg.svd(xx,compute_uv=False)
 b=np.linalg.lstsq(xx,yy,rcond=None)[0]
 normal=float(np.max(np.abs(xx.T@(yy-xx@b))))
 diag={'species':sp,'response':response,'deleted_year':dropyear,'n':len(f),'positive_n':int((f[sp]>0).sum()),'positions':f.position.nunique(),'parents':f.parent_id.nunique(),'years':f.year.nunique(),'rank':rank,'expected_rank':5,'condition':float(sv[0]/sv[-1]) if sv[-1]>0 else None,'projection_iterations':it,'projection_error':err,'normal_equation_error':normal,'status':'ESTIMATED_DESCRIPTIVE_FE' if rank==5 else 'RANK_DEFICIENT_DO_NOT_INTERPRET'}
 # Recover the nuisance fit only for prediction-range and residual-dependence diagnostics.
 r=y-X@b; alpha=np.zeros(len(f));codesp=pd.factorize(f.position,sort=True)[0];codesy=pd.factorize(f.year,sort=True)[0]
 ap=np.zeros(codesp.max()+1);ay=np.zeros(codesy.max()+1)
 for _ in range(1000):
  old=alpha.copy();ap=np.bincount(codesp,weights=r-ay[codesy])/np.bincount(codesp);ay=np.bincount(codesy,weights=r-ap[codesp])/np.bincount(codesy);alpha=ap[codesp]+ay[codesy]
  if np.max(np.abs(alpha-old))<1e-11:break
 pred=X@b+alpha;res=y-pred
 diag.update({'fitted_min':float(pred.min()),'fitted_max':float(pred.max()),'outside_probability_range_n':int(((pred<0)|(pred>1)).sum()) if response=='recorded_positive' else None,'residual_sd':float(res.std()),'census_residual_mean_max_abs':float(pd.DataFrame({'r':res,'census':f.census_id.to_numpy()}).groupby('census').r.mean().abs().max())})
 rows=[{'species':sp,'response':response,'category':c,'reference_category':0,'estimate':float(b[c-1]) if rank==5 else None,'deleted_year':dropyear,'n':len(f),'status':diag['status']} for c in range(1,6)]
 return rows,diag

coefs=[];diagnostics=[];sens=[]
for sp in taxa:
 for response in ['recorded_positive','positive_log_count']:
  rr,dd=fit_frame(known,sp,response);coefs+=rr;diagnostics.append(dd)
  for year in range(2013,2024):
   rr,dd=fit_frame(known,sp,response,year);sens+=rr;diagnostics.append(dd)
save(pd.DataFrame(coefs),'FIELD_WATER_FE_COEFFICIENTS.csv')
save(pd.DataFrame(sens),'FIELD_WATER_FE_DELETE_YEAR.csv')
save(pd.DataFrame(diagnostics),'FIELD_WATER_FE_DIAGNOSTICS.csv')

# Same-water common support: each retained position receives weight 1/Ncommon,
# each water category within position receives its pooled E/L visit share.
common=[];standard=[];local=[]
for pos,gr in known.groupby('position',sort=True):
 cat=gr.groupby(['water_code','period']).size().unstack(fill_value=0)
 for c,r in cat.iterrows():
  if r.get('E',0)>0 and r.get('L',0)>0:
   common.append({'position':pos,'water_code':c,'E_n':int(r.E),'L_n':int(r.L),'pooled_n':int(r.E+r.L),'parent_id':gr.parent_id.iloc[0]})
cs=pd.DataFrame(common);cs['within_position_weight']=cs.pooled_n/cs.groupby('position').pooled_n.transform('sum')
save(cs,'COMMON_WATER_SUPPORT_STRATA.csv')
for sp in taxa:
 for row in cs.to_dict('records'):
  f=known[known.position.eq(row['position'])&known.water_code.eq(row['water_code'])]
  e=f[f.period.eq('E')][sp];l=f[f.period.eq('L')][sp]
  local.append(row|{'species':sp,'f_E':float((e>0).mean()),'f_L':float((l>0).mean()),'mu_E':float(e.mean()),'mu_L':float(l.mean()),'q_E':float(e[e>0].mean()) if (e>0).any() else None,'q_L':float(l[l>0].mean()) if (l>0).any() else None,'delta_f':float((l>0).mean()-(e>0).mean()),'delta_mu':float(l.mean()-e.mean())})
 loc=pd.DataFrame([r for r in local if r['species']==sp]); npcs=cs.position.nunique()
 sub=known[known.position.isin(cs.position)]
 common_sub=known.merge(cs[['position','water_code']],on=['position','water_code'],validate='many_to_one')
 for metric in ['f','mu']:
  vals={p:float((loc[f'{metric}_{p}']*loc.within_position_weight).sum()/npcs) for p in ['E','L']}
  raw={p:float((sub[sub.period.eq(p)][sp]>0).mean() if metric=='f' else sub[sub.period.eq(p)][sp].mean()) for p in ['E','L']}
  matched={}
  for p in ['E','L']:
   ff=common_sub[common_sub.period.eq(p)].copy();ff['_response']=(ff[sp]>0).astype(float) if metric=='f' else ff[sp]
   matched[p]=float(ff.groupby('position')._response.mean().mean())
  standard.append({'species':sp,'metric':metric,'common_positions':npcs,'common_strata':len(cs),'parents':cs.parent_id.nunique(),'standardized_E':vals['E'],'standardized_L':vals['L'],'standardized_delta':vals['L']-vals['E'],'same_common_strata_unstandardized_E':matched['E'],'same_common_strata_unstandardized_L':matched['L'],'same_common_strata_unstandardized_delta':matched['L']-matched['E'],'same_position_all_category_unstandardized_E':raw['E'],'same_position_all_category_unstandardized_L':raw['L'],'same_position_all_category_unstandardized_delta':raw['L']-raw['E'],'note':'POOLED_COMMON_CATEGORY_WEIGHTS_WITHIN_POSITION;THEN_EQUAL_POSITION_WEIGHT;DESCRIPTIVE_NOT_CAUSAL'})
save(pd.DataFrame(local),'COMMON_WATER_STRATUM_RESULTS.csv');save(pd.DataFrame(standard),'COMMON_WATER_STANDARDIZED_PERIOD_RESULTS.csv')
# Full sample category response profiles and subset-matched no-environment baseline.
profiles=[];baseline=[]
for sp in taxa:
 for (period,c),f in known.groupby(['period','water_code']):
  v=f[sp];profiles.append({'species':sp,'period':period,'water_code':c,'n':len(f),'positive_n':int((v>0).sum()),'f':float((v>0).mean()),'mu':float(v.mean()),'q':float(v[v>0].mean()) if (v>0).any() else None})
 for scope,frame in [('G2_ALL',d),('KNOWN_WATER_SAME_SUBSET',known)]:
  for p,f in frame.groupby('period'):
   v=f[sp];baseline.append({'species':sp,'scope':scope,'period':p,'n':len(f),'f':float((v>0).mean()),'mu':float(v.mean()),'q':float(v[v>0].mean()) if (v>0).any() else None})
save(pd.DataFrame(profiles),'FIELD_WATER_CATEGORY_RESPONSE_PROFILES.csv');save(pd.DataFrame(baseline),'ENVIRONMENT_SUBSET_BASELINE.csv')
(SUP/'RUN_SUMMARY.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'pandas':pd.__version__,'numpy':np.__version__,'coefficient_rows':len(coefs),'sensitivity_rows':len(sens),'all_rank5':all(r['rank']==5 for r in diagnostics),'max_normal_equation_error':max(r['normal_equation_error'] for r in diagnostics),'common_positions':int(cs.position.nunique()),'common_strata':len(cs),'new_environment_relationships':1,'random_seed':'NOT_APPLICABLE_DETERMINISTIC','inference':'FINITE_OBSERVED_DESCRIPTIVE_FE;NO_P_VALUES_OR_GENERAL_POPULATION_CI','sources':SOURCES},ensure_ascii=False,indent=2),encoding='utf-8')
print('Environment estimates and registered delete-year sensitivities completed.')
