from bridge_common import *
assert json.loads((ROOT/'support/BASELINE_GATE.json').read_text())['status']=='PASS'
plan=ROOT/'design/ANALYSIS_PLAN_LOCK.md'
gate=ROOT/'support/ANALYSIS_LOCK_RECEIPT.json'
if gate.exists():assert json.loads(gate.read_text())['plan_sha256']==sha(plan)
else:jout('support/ANALYSIS_LOCK_RECEIPT.json',dict(locked_utc=now(),plan_sha256=sha(plan),baseline='PASS',new_effect_estimation_started_after_lock=True))
groups={'parent_month':['parent_id','parent_name','parent_code','month'],'child':['parent_id','parent_name','parent_code','child_id','child_name'],'parent':['parent_id','parent_name','parent_code'],'month':['month'],'window':['window']}
scenario_stats=[];scenario_parents=[];scenario_pm=[];scenario_windows=[];scenario_hhi=[];scenario_hierarchy=[];scenario_positions=[]
def attach_windows(f):
 f=f.copy();mapping={m:w for w,ms in WINDOWS.items() if w!='ANNUAL' for m in ms};f['window']=f.month.map(mapping);return f
def contribution_groups(f,pos,sp,columns,N):
 ag=pos.groupby(columns,dropna=False).agg(a_E=('a_E','sum'),a_L=('a_L','sum'),signed_contribution=('d','sum'),N_group=('position','size'),Pplus=('d',lambda a:a.clip(lower=0).sum()),Pminus=('d',lambda a:a.clip(upper=0).sum())).reset_index()
 ag['internal_mean_E']=ag.a_E/ag.N_group;ag['internal_mean_L']=ag.a_L/ag.N_group
 ag['internal_delta_mu']=ag.internal_mean_L-ag.internal_mean_E;ag['raw_sum_delta']=ag.a_L-ag.a_E;ag['position_weight']=ag.N_group/N
 for label,flag in [('E',f.year<=f.attrs['cutoff']),('L',f.year>f.attrs['cutoff'])]:
  x=f[flag].copy();x['positive']=x[sp]>0
  st=x.groupby(columns,dropna=False).agg(slot_n=(sp,'size'),positive_n=('positive','sum'),value_sum=(sp,'sum')).reset_index()
  st['f']=st.positive_n/st.slot_n;st['q']=st.value_sum/st.positive_n.replace(0,np.nan);st['zero_n']=st.slot_n-st.positive_n
  st=st.rename(columns={c:c+'_'+label for c in ['slot_n','positive_n','value_sum','f','q','zero_n']})
  ag=ag.merge(st,on=columns,validate='one_to_one')
 ag['local_Cf']=(ag.f_L-ag.f_E)*(ag.q_L+ag.q_E)/2;ag['local_Cq']=(ag.q_L-ag.q_E)*(ag.f_L+ag.f_E)/2
 ag['weighted_local_Cf']=ag.local_Cf*ag.position_weight;ag['weighted_local_Cq']=ag.local_Cq*ag.position_weight
 ag['q_state']=np.where(ag.q_E.notna()&ag.q_L.notna(),'BOTH_PERIODS_POSITIVE',np.where(ag.positive_n_E+ag.positive_n_L>0,'ONE_PERIOD_POSITIVE','BOTH_ZERO'))
 ag['unsplit_contribution']=np.where(ag.q_state!='BOTH_PERIODS_POSITIVE',ag.signed_contribution,0.)
 ag['species']=sp
 ag['negative_net_group_sign_share']=(-ag.signed_contribution.clip(upper=0))/(-ag.signed_contribution.clip(upper=0).sum()) if (ag.signed_contribution<0).any() else np.nan
 ag['positive_net_group_sign_share']=ag.signed_contribution.clip(lower=0)/ag.signed_contribution.clip(lower=0).sum() if (ag.signed_contribution>0).any() else np.nan
 ag['negative_mass_share']=ag.Pminus/ag.Pminus.sum() if ag.Pminus.sum()<0 else np.nan
 ag['positive_mass_share']=ag.Pplus/ag.Pplus.sum() if ag.Pplus.sum()>0 else np.nan
 return ag
def analyze(config,label,cutoff=2017,omit=None,full=False):
 f=attach_windows(load(config));f=f[f.year!=omit].copy() if omit else f;f.attrs['cutoff']=cutoff
 N=f.position.nunique();early=f[f.year<=cutoff];late=f[f.year>cutoff]
 index=['position','parent_id','parent_name','parent_code','child_id','child_name','month','window']
 pa_all=[];pm_all=[];win_all=[];pos_all=[];ch_all=[];mon_all=[];stats_all=[];hhi_all=[];hier_all=[];cparents=[];cchildren=[]
 for sp in SPECIES:
  p=early.groupby(index)[sp].mean().rename('a_E').reset_index().merge(late.groupby(index)[sp].mean().rename('a_L').reset_index(),on=index,validate='one_to_one')
  p['raw_delta']=p.a_L-p.a_E;p['d']=p.raw_delta/N;p['species']=sp;pos_all.append(p)
  e=stat(early[sp]);l=stat(late[sp]);s=dict(scenario=label,configuration=config,cutoff=cutoff,omitted_year=omit,species=sp,N=N,early_years=early.year.nunique(),late_years=late.year.nunique(),**{'early_'+k:v for k,v in e.items()},**{'late_'+k:v for k,v in l.items()},**contrast(e,l),Pplus=p.d.clip(lower=0).sum(),Pminus=p.d.clip(upper=0).sum(),negative_positions=int((p.d<0).sum()),positive_positions=int((p.d>0).sum()),zero_change_positions=int((p.d==0).sum()))
  s['cancellation_fraction']=1-abs(s['delta_mu'])/(s['Pplus']-s['Pminus']) if s['Pplus']-s['Pminus']>0 else np.nan
  stats_all.append(s)
  for name,cols in groups.items():
   g=contribution_groups(f,p,sp,cols,N)
   g['scenario']=label;g['configuration']=config
   {'parent':pa_all,'parent_month':pm_all,'window':win_all,'child':ch_all,'month':mon_all}[name].append(g)
   if name in ('parent','parent_month','window'):
    err=abs(g.signed_contribution.sum()-s['delta_mu']);assert err<1e-10
    err2=abs(g.weighted_local_Cf.sum()+g.weighted_local_Cq.sum()+g.unsplit_contribution.sum()-s['delta_mu']);assert err2<1e-10
  for window,months in WINDOWS.items():
   x=f[f.month.isin(months)];ix=index[:-1] # window membership no ambiguity
   ne=x.position.nunique();en=early[early.month.isin(months)].groupby(ix)[sp].mean().reset_index();ln=late[late.month.isin(months)].groupby(ix)[sp].mean().reset_index()
   bych={};byp={};bys={}
   for period,z in [('E',en),('L',ln)]:
    ch,pa,su=concentration(z,sp);bych[period]=ch;byp[period]=pa;bys[period]=su
    common=dict(scenario=label,configuration=config,species=sp,window=window,period=period,N=ne,years=early.year.nunique() if period=='E' else late.year.nunique())
    hhi_all.append(dict(**common,**su))
    if full:cparents.append(pa.assign(**common));cchildren.append(ch.assign(**common))
   h=byp['E'].merge(byp['L'],on=['parent_id','parent_name','parent_code'],suffixes=('_E','_L'),validate='one_to_one')
   h['delta_Y']=h.Y_L-h.Y_E;h['d_parent']=h.delta_Y/ne;h['annual_network_contribution']=h.delta_Y/N;h['delta_W']=h.W_L-h.W_E;h['delta_K']=h.K_L-h.K_E
   pair=(h.Y_E>0)&(h.Y_L>0)
   h['between']=(h.W_L**2-h.W_E**2)*(h.H_E+h.H_L)/2
   h['within']=(h.H_L-h.H_E)*(h.W_E**2+h.W_L**2)/2
   h['entry_exit']=np.where(pair,0.,h.delta_K)
   h['decomposition_state']=np.where(pair,'PAIRED_POSITIVE','ENTRY_EXIT_OR_BOTH_ZERO')
   h['scenario']=label;h['configuration']=config;h['species']=sp;h['window']=window;hier_all.append(h)
   assert abs(h.delta_K.sum()-(bys['L']['HHI_child']-bys['E']['HHI_child']))<1e-10 or not np.isfinite(bys['E']['HHI_child']) or not np.isfinite(bys['L']['HHI_child'])
   assert np.nanmax(abs(h.delta_K-(h.between.fillna(0)+h.within.fillna(0)+h.entry_exit)))<1e-10 or h.delta_K.isna().all()
 pa=pd.concat(pa_all);pm=pd.concat(pm_all);wi=pd.concat(win_all)
 scenario_stats.extend(stats_all);scenario_parents.append(pa);scenario_pm.append(pm);scenario_windows.append(wi);scenario_hhi.extend(hhi_all);scenario_hierarchy.append(pd.concat(hier_all))
 scenario_positions.append(pd.concat(pos_all).assign(scenario=label,configuration=config))
 if full:
  for name,data in [('POSITION_SIGNED_CONTRIBUTIONS',pos_all),('PARENT_MONTH_CONTRIBUTIONS',pm_all),('CHILD_CONTRIBUTIONS',ch_all),('PARENT_CONTRIBUTIONS',pa_all),('MONTH_CONTRIBUTIONS',mon_all),('WINDOW_CONTRIBUTIONS',win_all)]:save('results/ground/'+name+'.csv',pd.concat(data))
  save('results/ground/ANNUAL_CHANGE_SUMMARY.csv',stats_all)
  save('results/concentration/PERIOD_PARENT_Y_W_H_K.csv',pd.concat(cparents));save('results/concentration/PERIOD_CHILD_Y_SHARES.csv',pd.concat(cchildren))
  save('results/concentration/PERIOD_HIERARCHY_DECOMPOSITION.csv',pd.concat(hier_all))
  save('results/concentration/PERIOD_HHI.csv',hhi_all)
  # Full annual records for every parent, parent×month and child; no data-based winner filtering.
  long=f.melt(id_vars=['year','position','parent_id','parent_name','parent_code','child_id','child_name','month','window'],value_vars=SPECIES,var_name='species',value_name='slot_mean')
  for name,cols in [('PARENT',['parent_id','parent_name','parent_code']),('PARENT_MONTH',['parent_id','parent_name','parent_code','month']),('CHILD',['parent_id','parent_name','parent_code','child_id','child_name'])]:
   out=long.groupby(['species','year']+cols).agg(Y=('slot_mean','sum'),mu=('slot_mean','mean'),N=('slot_mean','size'),positive_slots=('slot_mean',lambda a:(a>0).sum())).reset_index();save('results/ground/YEARLY_'+name+'_RECORDS.csv',out)
 print(label,'complete',flush=True)
analyze('G2','G2_MAIN',full=True)
analyze('G3','G3')
for y in range(2013,2024):analyze('G2','OMIT_'+str(y),omit=y)
for c in [2016,2018]:analyze('G2','CUTOFF_'+str(c),cutoff=c)
for name,data in [('ANNUAL_SUMMARY',pd.DataFrame(scenario_stats)),('PARENT',pd.concat(scenario_parents)),('PARENT_MONTH',pd.concat(scenario_pm)),('WINDOW',pd.concat(scenario_windows)),('POSITION',pd.concat(scenario_positions)),('HHI',pd.DataFrame(scenario_hhi)),('HIERARCHY',pd.concat(scenario_hierarchy))]:save('results/sensitivity/'+name+'_ALL_SCENARIOS.csv',data)
# Annual versus averaged period distributions are deliberately separate objects.
f=load();yearly=[];yp=[]
for sp in SPECIES:
 for window,months in WINDOWS.items():
  for y in range(2013,2024):
   x=f[(f.year==y)&f.month.isin(months)];_,pa,su=concentration(x,sp)
   yearly.append(dict(species=sp,window=window,year=y,**su,**stat(x[sp])))
   if window=='ANNUAL':yp.append(pa.assign(species=sp,year=y))
yearly=pd.DataFrame(yearly);save('results/concentration/YEARLY_HHI_AND_COMPONENTS.csv',yearly);save('results/concentration/YEARLY_PARENT_Y_W_H_K.csv',pd.concat(yp))
hp=pd.DataFrame(scenario_hhi);hp=hp[hp.scenario=='G2_MAIN'];comp=[]
for sp in SPECIES:
 for w in WINDOWS:
  a=yearly[(yearly.species==sp)&(yearly.window==w)];p=hp[(hp.species==sp)&(hp.window==w)]
  r=dict(species=sp,window=w)
  for h in ['HHI_child','HHI_parent']:
   for period,flag in [('E',a.year<=2017),('L',a.year>=2018)]:
    r[h+'_period_'+period]=p.loc[p.period==period,h].iloc[0];r[h+'_annual_mean_'+period]=a.loc[flag,h].mean()
    r[h+'_annual_defined_years_'+period]=int(a.loc[flag,h].notna().sum());r[h+'_annual_total_years_'+period]=int(flag.sum())
   r[h+'_2013']=a.loc[a.year==2013,h].iloc[0];r[h+'_2023']=a.loc[a.year==2023,h].iloc[0]
   r[h+'_endpoint_delta']=r[h+'_2023']-r[h+'_2013'];r[h+'_period_delta']=r[h+'_period_L']-r[h+'_period_E'];r[h+'_annual_mean_delta']=r[h+'_annual_mean_L']-r[h+'_annual_mean_E']
  comp.append(r)
save('results/concentration/PERIOD_ENDPOINT_ANNUAL_COMPARISON.csv',comp)
# Focused same-parent endpoint comparison for all13, not only historical exemplars.
yp=pd.concat(yp);end=yp[yp.year==2013].merge(yp[yp.year==2023],on=['species','parent_id','parent_code','parent_name'],suffixes=('_2013','_2023'))
for k in ['Y','W','H','K']:end['endpoint_delta_'+k]=end[k+'_2023']-end[k+'_2013']
main=pd.concat(scenario_hierarchy);main=main[(main.scenario=='G2_MAIN')&(main.window=='ANNUAL')]
save('results/concentration/PARENT_PERIOD_ENDPOINT_COMPARISON.csv',main.merge(end,on=['species','parent_id','parent_code','parent_name'],validate='one_to_one'))
jout('support/GROUND_RUN_COMPLETED.json',dict(completed_utc=now(),scenarios=15,all_species=len(SPECIES),windows=list(WINDOWS),plan_sha256=sha(plan),randomness=False,seed=None))
