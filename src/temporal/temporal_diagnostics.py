from analysis_lib import *
gate();assert readj(S/'BASELINE_GATES.json')['branches']['A1']['status']=='PASS'
T=O/'02_TEMPORAL_TREND_DIAGNOSTICS';a=air_load();z,b=air_departures(a)
def decyear(d):
 dt=pd.to_datetime(d);ys=pd.to_datetime(dt.dt.year.astype(str)+'-01-01');ye=pd.to_datetime((dt.dt.year+1).astype(str)+'-01-01');return dt.dt.year+(dt-ys).dt.total_seconds()/(ye-ys).dt.total_seconds()
def fit_trends(data):
 out=[];params=[]
 for (sec,s),zz in data[data.departure.notna()].groupby(['parent_id','species']):
  zz=zz.copy();n_y=zz.groupby('year').unit.transform('size');w=1/n_y.to_numpy(float);x=decyear(zz.actual_date).to_numpy(float);y=zz.departure.to_numpy(float)
  assert zz.year.nunique()>=3
  xc=float(np.dot(w,x)/w.sum());yc=float(np.dot(w,y)/w.sum());den=float(np.dot(w,(x-xc)**2));assert den>0
  slope=float(np.dot(w,(x-xc)*(y-yc))/den);res=y-yc-slope*(x-xc)
  if np.ptp(y)==0:res=np.zeros(len(y));slope=0.0
  zz['trend_residual']=res;out.append(zz)
  params.append(dict(sector=sec,species=s,n_events=len(zz),n_years=zz.year.nunique(),years=';'.join(map(str,sorted(zz.year.unique()))),total_weight=float(w.sum()),weight_rule='1/n_departure_events_in_observed_year',center_decimal_year=xc,intercept_at_center=yc,slope_per_decimal_year=slope,weighted_residual_mean=float(np.dot(w,res)/w.sum()),weighted_residual_time_covariance=float(np.dot(w,res*(x-xc))/w.sum()),weighted_SSE=float(np.dot(w,res**2)),original_weighted_SST=float(np.dot(w,(y-yc)**2))))
 return pd.concat(out,ignore_index=True),params
zf,params=fit_trends(z)
csvout(T/'07_YEAR_BALANCED_TREND_PARAMETERS.csv',params)
meta=a.set_index(['parent_id','unit'])
fullpiv=air_pivots(z);fullshared=set(fullpiv['PNC'].index)&set(fullpiv['SB'].index)
primaryrho={(r['sector'],r['scenario'],r['species_a'],r['species_b']):r['rho'] for r in air_pair_rows(z)}
def compare(data,value,scenario_labels=('NATIVE_SUPPORT','COMMON_EVENTS_NATIVE_BASELINE_RETAINED')):
 piv=air_pivots(data,value);orig=air_pivots(data,'departure');shared=set(piv['PNC'].index)&set(piv['SB'].index);rows=[]
 for sec in ['PNC','SB']:
  for scenario,ids in [(scenario_labels[0],set(piv[sec].index)),(scenario_labels[1],shared)]:
   ids=sorted(ids);d=piv[sec].loc[ids];before=orig[sec].loc[ids];years=meta.loc[[(sec,u) for u in ids],'year'];months=meta.loc[[(sec,u) for u in ids],'month']
   for s,t in itertools.combinations(AIRSPEC,2):
    valid=d[[s,t]].notna().all(axis=1)&before[[s,t]].notna().all(axis=1);indices=d.index[valid];rr=rho(before.loc[indices,s],before.loc[indices,t]);ra=rho(d.loc[indices,s],d.loc[indices,t]);basis='NATIVE_SUPPORT' if scenario==scenario_labels[0] else 'COMMON_EVENTS_NATIVE_BASELINE_RETAINED';full=primaryrho[sec,basis,s,t]
    rows.append(dict(sector=sec,scenario=scenario,species_a=s,species_b=t,original_rho=rr,adjusted_rho=ra,delta_rho=ra-rr if ra is not None and rr is not None else None,original_sign=sign(rr),adjusted_sign=sign(ra),n_paired_events=len(indices),n_supported_years=int(years.nunique()),supported_years=';'.join(map(str,sorted(years.unique()))),calendar_months=';'.join(map(str,sorted(months.unique()))),original_full_comparison_rho=full,original_comparison_minus_full=rr-full if rr is not None else None,adjustment=value,value_state='DEFINED_DESCRIPTIVE' if ra is not None else 'UNDEFINED_CONSTANT_RANKS_OR_INSUFFICIENT_PAIRS'))
 return rows
primary=compare(zf,'trend_residual')
# Source-support tables include all 264 year-month cells, preserving no-observation states.
support=[];year_summary=[];confounding=[]
for sec in ['PNC','SB']:
 aa=a[a.parent_id==sec];dd=zf[(zf.parent_id==sec)&(zf.species==AIRSPEC[0])]
 ny=aa.groupby('month').year.nunique().to_dict();dep_ids=set(dd.unit)
 for y in YEARS:
  yy=aa[aa.year==y];yd=dd[dd.year==y];year_summary.append(dict(sector=sec,year=y,full_events=len(yy),departure_events=len(yd),distinct_months=yd.month.nunique(),within_year_qualified=bool(len(yd)>=3 and yd.month.nunique()>=3)))
  for m in range(1,13):
   ss=yy[yy.month==m];de=ss[ss.unit.isin(dep_ids)];yrs=sorted(aa.loc[aa.month==m,'year'].unique())
   support.append(dict(sector=sec,year=y,month=m,n_full_eligible_events=len(ss),n_departure_events=len(de),n_shared_departure_events=int(ss.unit.isin(fullshared).sum()) if m in set(dd.month) else 0,distinct_reference_years=ny.get(m,0),reference_years=';'.join(map(str,yrs)),reportable_min3=ny.get(m,0)>=3,reportable_min4=ny.get(m,0)>=4,reportable_min5=ny.get(m,0)>=5,observation_state='OBSERVED_ELIGIBLE_EVENT' if len(ss) else 'NO_INCLUDED_EVENT_NOT_ZERO_BIRDS',period='EARLY_2013_2017' if y<=2017 else 'LATE_2018_2023'))
 x=decyear(dd.actual_date).to_numpy(float);grand=x.mean();total=float(np.sum((x-grand)**2));between=sum(len(v)*(decyear(v.actual_date).mean()-grand)**2 for _,v in dd.groupby('month'))
 confounding.append(dict(sector=sec,n_events=len(dd),n_years=dd.year.nunique(),calendar_month_group_eta_squared=float(between/total),early_departure_events=int((dd.year<=2017).sum()),late_departure_events=int((dd.year>=2018).sum()),early_years=';'.join(map(str,sorted(dd.loc[dd.year<=2017,'year'].unique()))),late_years=';'.join(map(str,sorted(dd.loc[dd.year>=2018,'year'].unique()))),single_event_years=';'.join(str(r['year']) for r in year_summary if r['sector']==sec and r['departure_events']==1),less_than_three_event_years=';'.join(str(r['year']) for r in year_summary if r['sector']==sec and r['departure_events']<3)))
csvout(T/'01_A1_YEAR_MONTH_SUPPORT.csv',support);csvout(T/'08_YEARLY_REPEAT_SUPPORT.csv',year_summary);csvout(T/'09_MONTH_YEAR_CONFOUNDING_DESCRIPTORS.csv',confounding)
# Predetermined secondary repeated-year subset, no singleton-zero artifacts.
within=[];infeasible=[];parts=[]
for sec in ['PNC','SB']:
 qualifying=[r['year'] for r in year_summary if r['sector']==sec and r['within_year_qualified']]
 zz=z[(z.parent_id==sec)&z.year.isin(qualifying)&z.departure.notna()].copy()
 if len(qualifying)<3 or zz.unit.nunique()<9:infeasible.append(dict(diagnostic='WITHIN_YEAR_CENTERING',sector=sec,reason='Fewer than three repeated-observation years or nine events',years=qualifying));continue
 zz['within_year_residual']=zz.departure-zz.groupby(['parent_id','species','year']).departure.transform('mean');parts.append(zz)
if len(parts)==2:within=compare(pd.concat(parts,ignore_index=True),'within_year_residual',('WITHIN_YEAR_REPEAT_SUPPORT','WITHIN_YEAR_SHARED_SUPPORT'))
elif parts:infeasible.append(dict(diagnostic='WITHIN_YEAR_COMPARISON',reason='One sector fails prespecified gate; no invented cross-sector common diagnostic'))
csvout(T/'02_ORIGINAL_VS_TREND_ADJUSTED_PAIRS.csv',primary+within)
# Reference threshold sensitivities alter reportability, not retained month medians.
thresholds=[]
for th in [3,4,5]:
 zz,bb=air_departures(a,th);piv=air_pivots(zz);shared=set(piv['PNC'].index)&set(piv['SB'].index)
 for (sec,s),q in bb[bb.reportable].groupby(['parent_id','species']):
  orig=b[(b.parent_id==sec)&(b.species==s)&b.reportable];q=q.sort_values('month');peaks=sorted(q.loc[q.median_log1p==q.median_log1p.max(),'month']);origpeaks=sorted(orig.loc[orig.median_log1p==orig.median_log1p.max(),'month'])
  thresholds.append(dict(sector=sec,species=s,min_sampled_years=th,n_reportable_months=len(q),reportable_months=';'.join(map(str,q.month)),lost_months_vs_min3=';'.join(map(str,sorted(set(orig.month)-set(q.month)))),peak_months=';'.join(map(str,peaks)),peak_changed_vs_min3=peaks!=origpeaks,n_tied_peaks=len(peaks),amplitude_log1p=float(q.median_log1p.max()-q.median_log1p.min()) if len(q)>=9 else None,amplitude_state='DEFINED' if len(q)>=9 else 'UNDEFINED_FEWER_THAN_NINE_REPORTABLE_MONTHS',n_departure_events=len(piv[sec]),n_shared_events=len(shared),retained_month_medians_changed=False))
csvout(T/'06_MONTHLY_REFERENCE_THRESHOLD_SENSITIVITY.csv',thresholds)
# Two predeclared year deletion policies, all years, all pairs, no result-based tuning.
influence=[]
for omitted in sorted(a.year.unique()):
 for policy in ['FIXED_ORIGINAL_MONTH_REFERENCES','RECOMPUTED_MIN3_MONTH_REFERENCES']:
  aa=a[a.year!=omitted].copy()
  if policy.startswith('FIXED'):zz=z[z.year!=omitted].copy();bb=b
  else:zz,bb=air_departures(aa)
  ff,pp=fit_trends(zz);rows=compare(ff,'trend_residual')
  for r in rows:
   sec=r['sector'];s=r['species_a'];valid=bb[(bb.parent_id==sec)&(bb.species==s)&bb.reportable];original=b[(b.parent_id==sec)&(b.species==s)&b.reportable]
   ids=air_pivots(ff)[sec].index
   if r['scenario'].startswith('COMMON'):p=air_pivots(ff);ids=sorted(set(p['PNC'].index)&set(p['SB'].index))
   fixed=fullpiv[sec].loc[sorted(ids)]
   original_comparison_ids=set(fullpiv[sec].index) if r['scenario']=='NATIVE_SUPPORT' else fullshared
   n_removed=int(((a.parent_id==sec)&(a.year==omitted)&a.unit.isin(original_comparison_ids)).sum())
   influence.append(dict(omitted_year=int(omitted),reference_policy=policy,**r,n_full_eligible_events_after_deletion=int((aa.parent_id==sec).sum()),n_reportable_months=len(valid),reportable_months=';'.join(map(str,sorted(valid.month))),lost_reference_months=';'.join(map(str,sorted(set(original.month)-set(valid.month)))),rho_fixed_full_reference_on_same_ids=rho(fixed[r['species_a']],fixed[r['species_b']]),correlation_year_removed=n_removed>0,n_original_comparison_events_from_omitted_year=n_removed,monthly_reference_reestimated=policy.startswith('RECOMPUTED'),trend_refitted_year_balanced=True))
csvout(T/'04_YEAR_INFLUENCE_AND_REFERENCE_SUPPORT.csv',influence)
def summarize(rows):
 out=[]
 for sec in ['PNC','SB']:
  for scenario in sorted({r['scenario'] for r in rows}):
   zz=[r for r in rows if r['sector']==sec and r['scenario']==scenario]
   for mode,col in [('original','original_rho'),('adjusted','adjusted_rho')]:
    vals=[r[col] for r in zz if r[col] is not None]
    out.append(dict(sector=sec,scenario=scenario,mode=mode,n_pairs=len(zz),n_defined=len(vals),n_positive=sum(v>0 for v in vals),n_negative=sum(v<0 for v in vals),n_zero=sum(v==0 for v in vals),median=float(np.median(vals)) if vals else None,minimum=min(vals) if vals else None,maximum=max(vals) if vals else None,n_events=sorted({r['n_paired_events'] for r in zz}),n_years=sorted({r['n_supported_years'] for r in zz})))
 return out
summary=summarize(primary+within);csvout(T/'10_SECTOR_COEFFICIENT_DISTRIBUTIONS.csv',summary)
infsummary=[]
for yr in sorted(a.year.unique()):
 for pol in ['FIXED_ORIGINAL_MONTH_REFERENCES','RECOMPUTED_MIN3_MONTH_REFERENCES']:
  for r in summarize([r for r in influence if r['omitted_year']==yr and r['reference_policy']==pol]):infsummary.append(dict(omitted_year=int(yr),reference_policy=pol,**r))
csvout(T/'11_YEAR_DELETION_DISTRIBUTIONS.csv',infsummary)
keys=[r for r in primary+within if (r['sector']=='PNC' and {r['species_a'],r['species_b']}=={'Fulica atra','Phoenicopterus roseus'}) or (r['sector']=='SB' and {r['species_a'],r['species_b']}=={'Ciconia ciconia','Phoenicopterus roseus'})]
jout(S/'TEMPORAL_RESULTS.json',dict(executed_utc=now(),primary_and_within_summary=summary,featured_pairs=keys,support_confounding=confounding,infeasible=infeasible,year_influence_rows=len(influence),primary_event_support_unchanged=True,threshold_rows=len(thresholds),randomness_used=False))
print(json.dumps(dict(summary=summary,featured_pairs=keys,support=confounding,threshold_peak_changes=[r for r in thresholds if r['peak_changed_vs_min3']]),ensure_ascii=False))
