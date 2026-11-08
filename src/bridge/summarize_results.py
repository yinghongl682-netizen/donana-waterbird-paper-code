from bridge_common import *
g=pd.read_csv(ROOT/'results/ground/ANNUAL_CHANGE_SUMMARY.csv');pm=pd.read_csv(ROOT/'results/ground/PARENT_MONTH_CONTRIBUTIONS.csv');pa=pd.read_csv(ROOT/'results/ground/PARENT_CONTRIBUTIONS.csv')
sens=pd.read_csv(ROOT/'results/sensitivity/PARENT_MONTH_ALL_SCENARIOS.csv');ps=pd.read_csv(ROOT/'results/sensitivity/PARENT_ALL_SCENARIOS.csv');ss=pd.read_csv(ROOT/'results/sensitivity/ANNUAL_SUMMARY_ALL_SCENARIOS.csv');yy=pd.read_csv(ROOT/'results/ground/YEARLY_PARENT_MONTH_RECORDS.csv')
rows=[]
for _,r in pm.iterrows():
 a=sens[(sens.species==r.species)&(sens.parent_id==r.parent_id)&(sens.month==r.month)]
 y=yy[(yy.species==r.species)&(yy.parent_id==r.parent_id)&(yy.month==r.month)]
 em=y.loc[y.year<=2017,'Y'].mean();lm=y.loc[y.year>=2018,'Y'].mean()
 rows.append(dict(species=r.species,parent_id=r.parent_id,parent_name=r.parent_name,parent_code=r.parent_code,month=r.month,main_contribution=r.signed_contribution,min_contribution=a.signed_contribution.min(),max_contribution=a.signed_contribution.max(),positive_scenarios=int((a.signed_contribution>0).sum()),negative_scenarios=int((a.signed_contribution<0).sum()),zero_scenarios=int((a.signed_contribution==0).sum()),tested_scenarios=len(a),early_year_mean_Y=em,late_year_mean_Y=lm,late_years_above_early_mean=int(((y.year>=2018)&(y.Y>em)).sum()),late_years_with_positive_Y=int(((y.year>=2018)&(y.Y>0)).sum())))
save('results/sensitivity/PARENT_MONTH_STABILITY_SUMMARY.csv',rows)
summary=[]
for _,r in g.iterrows():
 a=pm[pm.species==r.species];neg=a[a.signed_contribution<0].sort_values('signed_contribution');pos=a[a.signed_contribution>0].sort_values('signed_contribution',ascending=False)
 q=ss[ss.species==r.species]
 summary.append(dict(species=r.species,delta_mu=r.delta_mu,Pplus=r.Pplus,Pminus=r.Pminus,negative_positions=r.negative_positions,positive_positions=r.positive_positions,negative_parent_month_groups=len(neg),positive_parent_month_groups=len(pos),negative_parent_groups=int(((pa.species==r.species)&(pa.signed_contribution<0)).sum()),positive_parent_groups=int(((pa.species==r.species)&(pa.signed_contribution>0)).sum()),top3_negative_net_PM_share=-neg.head(3).signed_contribution.sum()/(-neg.signed_contribution.sum()) if len(neg) else np.nan,top3_negative_PM_position_mass_share=-neg.head(3).Pminus.sum()/(-r.Pminus) if r.Pminus<0 else np.nan,top3_positive_net_PM_share=pos.head(3).signed_contribution.sum()/pos.signed_contribution.sum() if len(pos) else np.nan,top_negative_parent_month='; '.join(f'{x.parent_name}/{int(x.month)} ({x.signed_contribution:+.4f})' for _,x in neg.head(3).iterrows()),top_positive_parent_month='; '.join(f'{x.parent_name}/{int(x.month)} ({x.signed_contribution:+.4f})' for _,x in pos.head(3).iterrows()),sensitivity_min=q.delta_mu.min(),sensitivity_max=q.delta_mu.max(),negative_scenarios=int((q.delta_mu<0).sum()),positive_scenarios=int((q.delta_mu>0).sum())))
save('results/ground/ALL13_SCIENTIFIC_PATTERN_SUMMARY.csv',summary)
rank=[]
for sp in SPECIES:
 base=ps[(ps.species==sp)&(ps.scenario=='G2_MAIN')][['parent_id','signed_contribution']].rename(columns={'signed_contribution':'main'})
 for scenario,a in ps[ps.species==sp].groupby('scenario'):
  t=base.merge(a[['parent_id','signed_contribution']],on='parent_id');rho=t.main.rank().corr(t.signed_contribution.rank())
  rank.append(dict(species=sp,scenario=scenario,parent_signed_contribution_rank_rho=rho,parents_compared=len(t),changed_direction_parents=int((np.sign(t.main)!=np.sign(t.signed_contribution)).sum())))
save('results/sensitivity/PARENT_RANK_AND_DIRECTION_STABILITY.csv',rank)
print(pd.DataFrame(summary)[['species','negative_positions','positive_positions','top3_negative_net_PM_share','sensitivity_min','sensitivity_max']].to_string(index=False))
