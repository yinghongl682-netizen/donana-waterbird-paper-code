from pathlib import Path

import argparse, hashlib, json, sys, math, itertools

from datetime import datetime, timezone

import pandas as pd

import numpy as np

def receipt(p):
    st=p.stat(); return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':st.st_size,'mtime_ns':st.st_mtime_ns}

def write(d,p):
    pd.DataFrame(d).to_csv(p,index=False,encoding='utf-8-sig')

def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,list):return [clean(x) for x in v]
    if isinstance(v,np.integer):return int(v)
    if isinstance(v,np.floating):v=float(v)
    if isinstance(v,float) and not math.isfinite(v):return None
    return v

def js(d,p):p.write_text(json.dumps(clean(d),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')

def stats(y,w=None):
    y=np.asarray(y,dtype=float);w=np.full(len(y),1/len(y)) if w is None else np.asarray(w,float)
    assert abs(w.sum()-1)<1e-12
    f=float(sum(w[y>0]));mu=float(np.dot(y,w));q=mu/f if f>0 else np.nan
    return {'frequency':f,'mean_count':mu,'positive_mean':q,'n_opportunities':len(y),'n_positive':int(sum(y>0)),'max_weight':float(w.max()),'positive_mean_state':'QUALIFIED' if f>0 else 'NOT_ESTIMABLE_NO_POSITIVE_RECORDS'}

def weighted_air(d,months):
    assert set(d.month)==set(months)
    w=1/len(months)/d.groupby('month').year.transform('nunique')/d.groupby(['month','year']).unit.transform('size')
    return stats(d.y,w)

def rank_pure(values):
    pairs=sorted(enumerate(values),key=lambda z:z[1]);rank=[0.0]*len(values);i=0
    while i<len(pairs):
        j=i+1
        while j<len(pairs) and pairs[j][1]==pairs[i][1]:j+=1
        mid=(i+1+j)/2
        for ix,_ in pairs[i:j]:rank[ix]=mid
        i=j
    return rank

def pearson_pure(a,b):
    n=len(a);ma=sum(a)/n;mb=sum(b)/n
    cov=sum((x-ma)*(y-mb) for x,y in zip(a,b));da=sum((x-ma)**2 for x in a);db=sum((y-mb)**2 for y in b)
    return cov/math.sqrt(da*db) if da>0 and db>0 else np.nan

SPECIES=['Ardea cinerea','Ciconia ciconia','Fulica atra','Himantopus himantopus','Limosa limosa','Phalacrocorax carbo','Phoenicopterus roseus','Platalea leucorodia','Recurvirostra avosetta']

def calculate(air,out,wide):
    air['L']=np.log1p(air.y)
    base=air.groupby(['parent_id','species','month']).agg(n_years=('year','nunique'),n_events=('unit','size'),median_log1p=('L','median')).reset_index()
    base['reference_state']=np.where(base.n_years>=3,'REPORTABLE','UNSUPPORTED_REFERENCE')
    base.loc[base.n_years<3,'median_log1p']=np.nan
    write(base,out/'native_data/ORIGINAL_AERIAL_CALENDAR_BASELINES.csv')
    a=air.merge(base[['parent_id','species','month','median_log1p']],on=['parent_id','species','month'],validate='many_to_one')
    a['departure']=a.L-a.median_log1p
    write(a,out/'native_data/ORIGINAL_AERIAL_NATIVE_DEPARTURES.csv')
    seasonal=[]
    for (sector,s),z in air.groupby(['parent_id','species']):
        b=base[(base.parent_id==sector)&(base.species==s)&base.median_log1p.notna()]
        seasonal.append({'species':s,'sector':sector,'n_eligible_events':len(z),'n_positive':int((z.y>0).sum()),'native_positive_frequency':float((z.y>0).mean()),'reportable_months':'|'.join(map(str,sorted(b.month))), 'n_reportable_months':len(b),'amplitude_log1p':float(b.median_log1p.max()-b.median_log1p.min()) if len(b)>=9 else None,'tied_peak_months':'|'.join(map(str,b[b.median_log1p==b.median_log1p.max()].month)),'year_counts_by_month':json.dumps(dict(zip(b.month.astype(str),b.n_years)),sort_keys=True)})
    write(seasonal,out/'native_data/ORIGINAL_AERIAL_SEASONAL_CONFIGURATIONS.csv')
    common=set(wide[wide.parent_id=='PNC'].unit)&set(wide[wide.parent_id=='SB'].unit)
    departures={sector:a[(a.parent_id==sector)&a.departure.notna()].pivot(index='unit',columns='species',values='departure') for sector in ['PNC','SB']}
    common=set.intersection(common,*[set(z.index) for z in departures.values()])
    rows=[];checks=[]
    for sector in ['PNC','SB']:
        for scenario in ['NATIVE_SUPPORT','COMMON_EVENTS_NATIVE_BASELINE_RETAINED']:
            d=departures[sector] if scenario=='NATIVE_SUPPORT' else departures[sector].loc[sorted(common)]
            for s,t in itertools.combinations(SPECIES,2):
                z=d[[s,t]].dropna();ra=z[s].rank(method='average');rb=z[t].rank(method='average');rho=float(np.corrcoef(ra,rb)[0,1]);ind=pearson_pure(rank_pure(z[s].tolist()),rank_pure(z[t].tolist()))
                rows.append({'sector':sector,'scenario':scenario,'species_a':s,'species_b':t,'n_paired_events':len(z),'rho':rho,'value_state':'QUALIFIED_DESCRIPTIVE','baseline':'NATIVE_SPECIES_SECTOR_MONTH_MEDIAN_RETAINED','role':'INHERITED_FINDING_RECOMPUTED' if scenario=='NATIVE_SUPPORT' else 'M9_NEW_ANALYSIS'})
                checks.append({'check':'independent_pure_python_average_ranks_and_pearson','sector':sector,'scenario':scenario,'species_a':s,'species_b':t,'absolute_error':abs(rho-ind),'pass':abs(rho-ind)<1e-12})
    corr=pd.DataFrame(rows);write(corr,out/'native_data/AERIAL_CORRESPONDENCE_NATIVE_AND_COMMON_SUPPORT.csv');write(checks,out/'qa/INDEPENDENT_RANK_ARITHMETIC_CHECKS.csv')
    corrsum=[]
    for (sector,scenario),d in corr.groupby(['sector','scenario']):corrsum.append({'sector':sector,'scenario':scenario,'n_pairs':len(d),'n_paired_events':int(d.n_paired_events.min()),'n_positive_pairs':int((d.rho>0).sum()),'n_negative_pairs':int((d.rho<0).sum()),'median_rho':float(d.rho.median()),'min_rho':float(d.rho.min()),'max_rho':float(d.rho.max())})
    write(corrsum,out/'native_data/AERIAL_CORRESPONDENCE_SUPPORT_SUMMARY.csv')
    commonmeta=wide[wide.unit.isin(common)][['unit','parent_id','actual_date','year','month']].sort_values(['actual_date','parent_id']);write(commonmeta,out/'native_data/AERIAL_COMMON_EVENT_SUPPORT.csv')
