from pathlib import Path
import pandas as pd,numpy as np,json,hashlib,sys,math
sys.stdout.reconfigure(encoding='utf-8')
from runtime_config import INPUT,OUTPUT
B=OUTPUT/'bridge';O=B/'results/cross_source';W=INPUT
assert (B/'code/cross_source/DATE_BOUNDARY_SENSITIVITY_ADDENDUM.md').exists()
v=pd.read_csv(B/'sources/QUALIFIED_VISITS_COUNTS.csv');slots=pd.read_csv(B/'sources/G2_SLOTS.csv');v=v[v.position.isin(slots.position)].copy();v['date']=pd.to_datetime(v.actual_date);v=v.set_index('opportunity_uid',drop=False)
roster=pd.read_csv(O/'FIXED_HISTORICALLY_NESTED_CHILD_MONTH_ROSTER.csv');a=pd.read_csv(OUTPUT/'aerial/A1_WIDE_COUNTS.csv').rename(columns={'unit':'event_id','parent_id':'sector'});a['date']=pd.to_datetime(a.actual_date)
mainvis=pd.read_csv(O/'ACTUAL_DATE_MATCHED_VISITS.csv');mainevents=pd.read_csv(O/'AERIAL_EVENT_COVERAGE_AND_DROPPED_SUPPORT.csv');bas=pd.read_csv(O/'NATIVE_MONTH_REFERENCES.csv');base=bas[bas.source.eq('AIR')].set_index(['sector','month','species']).median_log1p.to_dict();species=sorted(bas.species.unique())
kids={(sec,int(m)):set(z.child_id) for (sec,m),z in roster.groupby(['sector','month'])}
edges=[]
for ai,r in a.iterrows():
 for cid in sorted(kids.get((r.sector,int(r.month)),set())):
  z=v[v.child_id.eq(cid)].copy();z['gap']=(z.date-r.date).dt.days
  for uid,t in z[z.gap.abs()<=14].iterrows():edges.append({'ai':int(ai),'sector':r.sector,'event_id':r.event_id,'child_id':cid,'opportunity_uid':uid,'aerial_date':r.actual_date,'ground_date':t.actual_date,'actual_ground_month':int(t.month),'aerial_month':int(r.month),'signed_days':int(t.gap),'absolute_days':abs(int(t.gap))})
edges=sorted(edges,key=lambda x:(x['absolute_days'],x['ground_date'],x['opportunity_uid'],x['event_id']));assigned={};used=set()
for e in edges:
 k=e['ai'],e['child_id']
 if k not in assigned and e['opportunity_uid'] not in used:assigned[k]=e;used.add(e['opportunity_uid'])
coverage=[];matches=[]
for ai,r in a.iterrows():
 kk=kids.get((r.sector,int(r.month)),set());z=[assigned[ai,c] for c in sorted(kk) if (ai,c) in assigned];ok=bool(kk) and len(z)==len(kk)
 dates=[t['ground_date'] for t in z]
 coverage.append({'sector':r.sector,'event_id':r.event_id,'year':int(r.year),'aerial_date':r.actual_date,'aerial_month':int(r.month),'required_children':len(kk),'matched_children':len(z),'complete_14d':ok,'cross_month_visits':sum(t['actual_ground_month']!=t['aerial_month'] for t in z),'complete_7d':ok and all(t['absolute_days']<=7 for t in z),'complete_same_day':ok and all(t['absolute_days']==0 for t in z),'ground_date_min':min(dates,default=''),'ground_date_max':max(dates,default=''),'ground_date_span_days':(pd.Timestamp(max(dates))-pd.Timestamp(min(dates))).days if dates else np.nan,'max_absolute_days':max((t['absolute_days'] for t in z),default=np.nan)})
 for t in z:matches.append({**t,'kept_complete_event':ok})
coverage=pd.DataFrame(coverage);matches=pd.DataFrame(matches);matches.to_csv(O/'ALL_DATE_14D_MATCHED_VISITS.csv',index=False,encoding='utf-8-sig');coverage.to_csv(O/'ALL_DATE_14D_EVENT_COVERAGE.csv',index=False,encoding='utf-8-sig');assert not matches.opportunity_uid.duplicated().any()
vr=v.reset_index(drop=True);logbas={}
for (cid,m),z in vr.groupby(['child_id','month']):
 if z.year.nunique()>=3:
  for sp in species:logbas[cid,int(m),sp]=float(np.median(np.log1p(z[sp])))
def extract(vis,cov,label):
 output=[];good=cov[cov.complete_14d];ev=a.set_index(['sector','event_id'])
 for _,r in good.iterrows():
  z=vis[vis.sector.eq(r.sector)&vis.event_id.eq(r.event_id)];vv=v.loc[z.opportunity_uid];assert len(vv)==r.required_children
  for sp in species:
   gd=np.mean([np.log1p(float(t[sp]))-logbas[t.child_id,int(t.month),sp] for _,t in vv.iterrows()]);av=float(ev.loc[(r.sector,r.event_id),sp]);ad=np.log1p(av)-base.get((r.sector,int(ev.loc[(r.sector,r.event_id),'month']),sp),np.nan)
   output.append({'sector':r.sector,'event_id':r.event_id,'year':int(r.year),'species':sp,'matching':label,'ground_actual_month_visit_departure_mean':gd,'aerial_native_month_departure':ad,'ground_raw_mean':float(vv[sp].mean()),'aerial_count':av,'n_ground_visits':len(vv),'complete_7d':bool(r.complete_7d),'complete_same_day':bool(r.complete_same_day)})
 return pd.DataFrame(output)
maincov=mainevents.rename(columns={'month':'aerial_month'}).copy();maincov['complete_7d']=maincov.complete_14d&(maincov.within7_children==maincov.required_children)&(maincov.required_children>0);maincov['complete_same_day']=maincov.complete_14d&(maincov.same_day_children==maincov.required_children)&(maincov.required_children>0)
dd=pd.concat([extract(mainvis,maincov,'ORIGINAL_SAME_MONTH_CONTROL'),extract(matches,coverage,'ALL_DATE_NEAREST_14D')],ignore_index=True);dd.to_csv(O/'DATE_BOUNDARY_ALTERNATIVE_VISIT_DEPARTURES.csv',index=False,encoding='utf-8-sig')
rankchecks=[]
def pure_rank(x):
 q=sorted(enumerate(x),key=lambda z:z[1]);r=[0.]*len(q);i=0
 while i<len(q):
  j=i+1
  while j<len(q) and q[j][1]==q[i][1]:j+=1
  for ix,_ in q[i:j]:r[ix]=(i+1+j)/2
  i=j
 return r
def rho(z):
 z=z.dropna(subset=['ground_actual_month_visit_departure_mean','aerial_native_month_departure']);x=z.ground_actual_month_visit_departure_mean;y=z.aerial_native_month_departure
 if z.year.nunique()<3 or x.nunique()<2 or y.nunique()<2:return np.nan
 r=float(x.rank().corr(y.rank()));xx=pure_rank(x.tolist());yy=pure_rank(y.tolist());mx=sum(xx)/len(xx);my=sum(yy)/len(yy);pr=sum((a-mx)*(b-my) for a,b in zip(xx,yy))/math.sqrt(sum((a-mx)**2 for a in xx)*sum((b-my)**2 for b in yy));rankchecks.append({'sector':z.sector.iloc[0],'species':z.species.iloc[0],'matching':z.matching.iloc[0],'n_events':len(z),'absolute_error':abs(r-pr)});assert abs(r-pr)<1e-12;return r
ss=[];lo=[]
for (sec,sp,matching),z in dd.groupby(['sector','species','matching']):
 for scenario,tt in [('MAIN_14D',z),('WITHIN7D',z[z.complete_7d]),('SAME_DAY',z[z.complete_same_day])]:ss.append({'sector':sec,'species':sp,'matching':matching,'scenario':scenario,'n_events':len(tt),'n_years':tt.year.nunique(),'rho_departure':rho(tt),'ground_indicator':'MEAN_OF_ACTUAL_MONTH_CHILD_LOG1P_DEPARTURES'})
 if matching=='ALL_DATE_NEAREST_14D':
  for yr in sorted(z.year.unique()):
   zz=z[z.year!=yr];lo.append({'sector':sec,'species':sp,'deleted_year':int(yr),'n_events':len(zz),'n_years':zz.year.nunique(),'rho_departure':rho(zz)})
for (sec,sp),z in dd.groupby(['sector','species']):
 ids=set(z[z.matching.eq('ORIGINAL_SAME_MONTH_CONTROL')].event_id)&set(z[z.matching.eq('ALL_DATE_NEAREST_14D')].event_id)
 for matching,tt in z[z.event_id.isin(ids)].groupby('matching'):ss.append({'sector':sec,'species':sp,'matching':matching,'scenario':'COMMON_EVENT_SUPPORT_14D','n_events':len(tt),'n_years':tt.year.nunique(),'rho_departure':rho(tt),'ground_indicator':'MEAN_OF_ACTUAL_MONTH_CHILD_LOG1P_DEPARTURES'})
ss=pd.DataFrame(ss);ss.to_csv(O/'DATE_BOUNDARY_CORRESPONDENCE_SENSITIVITY.csv',index=False,encoding='utf-8-sig');pd.DataFrame(lo).to_csv(O/'ALL_DATE_LEAVE_YEAR_OUT.csv',index=False,encoding='utf-8-sig')
cmp=matches.merge(mainvis[['sector','event_id','child_id','opportunity_uid','kept_complete_event']],on=['sector','event_id','child_id'],how='outer',suffixes=('_all','_same'),indicator=True);cmp['same_assigned_visit']=cmp.opportunity_uid_all.eq(cmp.opportunity_uid_same);cmp.to_csv(O/'ALL_DATE_VS_SAME_MONTH_ASSIGNMENT_COMPARISON.csv',index=False,encoding='utf-8-sig')
su=[]
for sec in ['PNC','SB']:
 old=set(mainevents[mainevents.sector.eq(sec)&mainevents.complete_14d].event_id);new=set(coverage[coverage.sector.eq(sec)&coverage.complete_14d].event_id)
 su.append({'sector':sec,'same_month_complete_events':len(old),'all_date_complete_events':len(new),'added_events':'|'.join(sorted(new-old)),'lost_events':'|'.join(sorted(old-new)),'all_date_cross_month_visits_kept':int(((matches.sector==sec)&matches.kept_complete_event&matches.actual_ground_month.ne(matches.aerial_month)).sum()),'all_date7_complete_events':int((coverage.sector.eq(sec)&coverage.complete_7d).sum())})
pd.DataFrame(su).to_csv(O/'DATE_BOUNDARY_SUPPORT_CHANGE.csv',index=False,encoding='utf-8-sig');pd.DataFrame(rankchecks).to_csv(O/'DATE_BOUNDARY_INDEPENDENT_RANK_CHECKS.csv',index=False,encoding='utf-8-sig')
statepath=O/'MODULE_STATE.json';state=json.loads(statepath.read_text(encoding='utf-8'));state.update(date_boundary_sensitivity='EXECUTED_WITH_PRESERVED_MAIN_PLAN_AND_ALTERNATIVE_ACTUAL_MONTH_CHILD_INDICATOR',date_boundary_support=su,date_boundary_independent_rank_checks=len(rankchecks),date_boundary_maximum_rank_error=max((x['absolute_error'] for x in rankchecks),default=0),important_scope='Primary group-record departure and mean child departure are distinct estimands; spoonbill SB rho 0.3267 vs 0.0187 limits local synchrony claim',review_stop='AUTHOR_SCIENTIFIC_REVIEW_REQUIRED');statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(pd.DataFrame(su).to_string(index=False));print(ss[ss.scenario.eq('MAIN_14D')].to_string(index=False))
