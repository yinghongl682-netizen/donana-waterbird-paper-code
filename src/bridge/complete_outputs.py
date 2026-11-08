"""Recovered existing scientific delivery blocks; no new estimates or author prose."""
from bridge_common import *
O=ROOT/'results/environment'
a=pd.read_csv(O/'FIELD_WATER_FE_COEFFICIENTS.csv')

ss=pd.read_csv(O/'FIELD_WATER_FE_DELETE_YEAR.csv')

di=pd.read_csv(O/'FIELD_WATER_FE_DIAGNOSTICS.csv')

d=pd.read_csv(O/'ENVIRONMENT_NATIVE_ANALYSIS_VISITS.csv')

st=pd.read_csv(O/'COMMON_WATER_STANDARDIZED_PERIOD_RESULTS.csv')

r=ss.groupby(['species','response','category']).estimate.agg(delete_year_min='min',delete_year_max='max').reset_index()

z=a.merge(r,on=['species','response','category'],validate='one_to_one')

z['all_deleted_year_same_sign_as_main']=(z.estimate*z.delete_year_min>0)&(z.estimate*z.delete_year_max>0)

z.to_csv(O/'FIELD_WATER_COEFFICIENT_SENSITIVITY_SUMMARY.csv',index=False,encoding='utf-8-sig')

serial=[]

for sp,response in a[['species','response']].drop_duplicates().itertuples(index=False,name=None):
 f=d[d.known_water].copy()
 if response=='positive_log_count':f=f[f[sp]>0]
 beta=a[(a.species==sp)&(a.response==response)].sort_values('category').estimate.to_numpy();X=np.column_stack([(f.water_code.to_numpy()==c) for c in range(1,6)])
 y=(f[sp].to_numpy()>0).astype(float) if response=='recorded_positive' else np.log(f[sp].to_numpy());r=y-X@beta
 cp=pd.factorize(f.position,sort=True)[0];cy=pd.factorize(f.year,sort=True)[0];ap=np.zeros(cp.max()+1);ay=np.zeros(cy.max()+1)
 for _ in range(1000):
  old=ap[cp]+ay[cy];ap=np.bincount(cp,weights=r-ay[cy])/np.bincount(cp);ay=np.bincount(cy,weights=r-ap[cp])/np.bincount(cy)
  if np.max(np.abs(ap[cp]+ay[cy]-old))<1e-11:break
 f['residual']=r-ap[cp]-ay[cy];f=f.sort_values(['position','year']);prev=f.groupby('position')[['year','residual']].shift(1);ok=f.year.eq(prev.year+1)
 rho=float(np.corrcoef(f.loc[ok,'residual'],prev.loc[ok,'residual'])[0,1]) if ok.sum()>2 else None
 serial.append({'species':sp,'response':response,'adjacent_year_same_position_pairs':int(ok.sum()),'residual_same_position_adjacent_year_correlation':rho,'residual_census_mean_max_abs':float(f.groupby('census_id').residual.mean().abs().max()),'interpretation':'REMAINING_DEPENDENCE_DESCRIBED;NO_INDEPENDENT_SLOT_INFERENCE_OR_CAUSAL_CLAIM'})

pd.DataFrame(serial).to_csv(O/'RESIDUAL_DEPENDENCE_DIAGNOSTICS.csv',index=False,encoding='utf-8-sig')

excerpt=z[z.category.eq(3)].copy()

excerpt.to_csv(O/'ILLUSTRATIVE_MEDIO_VS_SECO_ALL13.csv',index=False,encoding='utf-8-sig')
g=pd.read_csv(ROOT/'results/ground/ANNUAL_CHANGE_SUMMARY.csv')

local=[]

for level in ['PARENT_MONTH','PARENT','CHILD','MONTH','WINDOW']:
 d=pd.read_csv(ROOT/f'results/ground/{level}_CONTRIBUTIONS.csv')
 for sp,a in d.groupby('species'):
  r=g[g.species==sp].iloc[0];z=dict(grouping=level,species=sp,weighted_local_Cf_sum=a.weighted_local_Cf.sum(),weighted_local_Cq_sum=a.weighted_local_Cq.sum(),unsplit_contribution_sum=a.unsplit_contribution.sum(),global_Cf=r.Cf,global_Cq=r.Cq,delta_mu=r.delta_mu,undefined_q_groups=int((a.q_state!='BOTH_PERIODS_POSITIVE').sum()))
  z['identity_error']=z['weighted_local_Cf_sum']+z['weighted_local_Cq_sum']+z['unsplit_contribution_sum']-r.delta_mu;local.append(z)

save('results/ground/LOCAL_DECOMPOSITION_RECONCILIATION.csv',local)

# Existing Stage6C scientific exports from freshly rebuilt A1 outputs.
from m9_original_blocks import stats
out=OUTPUT/'aerial/m9'
ns={'corr':pd.read_csv(out/'native_data/AERIAL_CORRESPONDENCE_NATIVE_AND_COMMON_SUPPORT.csv'),'air':pd.read_csv(out/'native_data/ORIGINAL_AERIAL_NATIVE_DEPARTURES.csv'),'stats':stats}
corr=ns['corr'].copy();corr['value_state']=np.where(corr.n_paired_events<3,'UNDEFINED_INSUFFICIENT_PAIRS',np.where(corr.rho.isna(),'UNDEFINED_CONSTANT_OR_UNSUPPORTED','QUALIFIED_DESCRIPTIVE'))
corr.to_csv(out/'native_data/CORRESPONDENCE_WITH_TYPED_STATES.csv',index=False,encoding='utf-8-sig')
summaries=[]
for (sec,s),d in ns['air'].groupby(['parent_id','species']):
    summaries.append({'sector':sec,'species':s,**ns['stats'](d.y),'n_zero':int((d.y==0).sum()),'actual_dates':'|'.join(sorted(d.actual_date))})
pd.DataFrame(summaries).to_csv(out/'native_data/FULL_EVENT_FREQUENCY_AND_CONDITIONAL_COUNTS.csv',index=False,encoding='utf-8-sig')
