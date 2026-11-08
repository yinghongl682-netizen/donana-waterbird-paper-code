"""Independent standard-library raw-source reconstruction, Stage 6D PATH B.
No PATH A import/read; no historical result read until independent outputs exist.
"""
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction as F
from decimal import Decimal
import csv,json,io,re,html,hashlib,datetime,sys
sys.dont_write_bytecode=True
sys.stdout.reconfigure(encoding='utf-8')
from runtime_config import INPUT,OUTPUT
OUT=OUTPUT/'bridge/sources'
PROJECT=INPUT
WORK=INPUT
RAW=INPUT/'raw_ground'
TAXA=sorted(['Ardea cinerea','Ciconia ciconia','Fulica atra','Himantopus himantopus','Limosa limosa','Phalacrocorax carbo','Phoenicopterus roseus','Platalea leucorodia','Recurvirostra avosetta','Netta rufina','Aythya ferina','Tadorna tadorna','Anas platyrhynchos'])
LEVELS=[f'Localidad nivel {i}' for i in range(1,5)]
YEARS=set(range(2013,2024))
WINDOWS={'ANNUAL':set(range(1,13)),'DJF':{12,1,2},'MarMay':{3,5},'JunJul':{6,7},'SON':{9,10,11}}
PARTIAL={'groundopp:582ba247afbada5d824ae453','groundopp:f6bd25a11fd47b0ef22e8655','groundopp:9982662b70a2631602cc474a'}
INPUTS={}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def enc(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def uid(prefix,x):return prefix+hashlib.sha256(enc(x).encode('utf-8')).hexdigest()[:24]
def readbytes(p):
 p=Path(p);b=p.read_bytes();h=hashlib.sha256(b).hexdigest();INPUTS[str(p)]=dict(sha256_before=h,read_utc=now(),bytes=len(b));return b
def readcsv(p):return list(csv.DictReader(io.StringIO(readbytes(p).decode('utf-8-sig'),newline='')))
def write(name,rows,fields=None):
 rows=list(rows);fields=fields or list(dict.fromkeys(k for r in rows for k in r))
 with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def jout(name,obj):(OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def exact_fields(d):
 o={}
 for k,v in d.items():
  if isinstance(v,F):o[k]=float(v);o[k+'_exact']=str(v)
  else:o[k]=v
 return o
def tax(r):return html.unescape(re.sub('<[^>]+>','',r['Especie'])).strip()
def key(r):return (r['Censo'],)+tuple(r[k] for k in LEVELS)
def sign(x):return 'UNDEFINED' if x is None else 'POSITIVE' if x>0 else 'NEGATIVE' if x<0 else 'ZERO'
def main():
 start=now();opp=defaultdict(list);counts=defaultdict(list);schemas=[];contracts=[];allcounts=Counter()
 for directory in sorted(RAW.iterdir()):
  if not directory.is_dir() or not re.fullmatch(r'CT_\d{6}',directory.name) or int(directory.name[3:7]) not in YEARS:continue
  for p in sorted(directory.iterdir()):
   if p.name.startswith(('02-','03-')) and p.suffix.lower()=='.csv':
    rr=readcsv(p);schemas.append(dict(path=str(p),rows=len(rr),header=enc(list(rr[0])) if rr else 'EMPTY'))
    for n,r in enumerate(rr,1):
     assert r['Censo']==directory.name,(p,n,r['Censo'])
     r0=dict(r);r['_locator']=str(p)+'#data_row='+str(n);r['_raw']=r0
     (opp if p.name.startswith('02-') else counts)[key(r)].append(r)
     allcounts[p.name[:2]]+=1
   elif p.name.lower()=='readme.md':
    t=readbytes(p).decode('utf-8-sig');contracts.append(dict(path=str(p),presence_only='solamente datos de presencia' in t,survey_join='cruzar la información' in t))
 assert all(r['presence_only'] and r['survey_join'] for r in contracts)
 contract=readcsv(INPUT/'contracts/ground_taxon_reporting.csv')
 assert {r['taxon'] for r in contract}==set(TAXA)
 assert all(r['eligibility']=='WITHIN_PROTOCOL_TARGET_SCOPE' for r in contract)
 audit=[];typed=[];exceptions=[];visits=[];unknown=[];duplicates=[]
 for k,rows in sorted(opp.items()):
  r=rows[0];raw=r['_raw'];contexts={enc({a:b for a,b in x['_raw'].items() if a!='Censadores'}) for x in rows}
  flags={x['Se censa'] for x in rows};survey=flags=={'Sí'} and len(contexts)==1
  oid=uid('groundopp:',list(k));child=uid('groundsite:',list(k[1:]));parent=uid('groundparent:',list(k[1:4]))
  date=r['Fecha'];date_state='BLANK';yr=int(k[0][3:7]);mo=int(k[0][7:9])
  if date:
   try:
    dt=datetime.date.fromisoformat(date);date_state='MATCH' if (dt.year,dt.month)==(yr,mo) else 'CENSUS_ACTUAL_MONTH_DIFFERENCE';yr,mo=dt.year,dt.month
   except ValueError:date_state='INVALID'
  water=re.fullmatch(r'.*\((\d+)\)',r['Nivel de agua']);watercode=int(water.group(1)) if water else None
  waterstate='KNOWN_CATEGORY' if watercode in range(6) else 'UNKNOWN_CATEGORY6' if watercode==6 else 'BLANK' if not r['Nivel de agua'] else 'UNRESOLVED_LABEL'
  cr=counts.get(k,[]);bytax=defaultdict(list)
  for x in cr:bytax[tax(x)].append(x)
  exactdup=Counter(enc(x['_raw']) for x in cr);dupnum=sum(v-1 for v in exactdup.values() if v>1)
  bad=[];parsed={}
  for tx,pp in bytax.items():
   nums=[]
   for x in pp:
    try:
     value=Decimal(x['Individuos']);assert value.is_finite() and value>=0 and value==value.to_integral_value();nums.append(int(value))
    except Exception:bad.append(x['_locator'])
   parsed[tx]=nums
  eligible=survey and date_state not in ('BLANK','INVALID') and yr in YEARS and not bad and not dupnum
  reason='ELIGIBLE_BIRD_ONLY' if eligible else 'CONTEXT_AMBIGUITY' if len(contexts)!=1 else 'UNSURVEYED_WITH_POSITIVE_CONFLICT' if flags!={'Sí'} and cr else 'UNSURVEYED' if flags!={'Sí'} else 'DATE_OR_COUNT_INVALID'
  base=dict(opportunity_uid=oid,census_id=k[0],actual_date=date,census_actual_date_state=date_state,year=yr,month=mo,child_id=child,parent_id=parent,position=child+'|'+str(mo).zfill(2),native_locality_key_json=enc(list(k[1:])),native_parent_key_json=enc(list(k[1:4])),locality_name=k[-1],survey_flags=enc(sorted(flags)),survey_qualified=survey,context_variants=len(contexts),native_row_count=len(rows),bird_eligible=eligible,known_water_eligible=eligible and watercode in range(6),water_code=watercode,water_state=waterstate,water_literal=r['Nivel de agua'],all_taxa_count_rows=len(cr),all_taxa_taxon_n=len(bytax),exact_duplicate_count_rows=dupnum,invalid_count_rows=len(bad),exclusion_reason=reason,con_aves=r['Con aves'],field_start=r['Inicio'],field_end=r['Fin'],visibility=r['Visibilidad'],wind=r['Viento'],temperature=r['Temperatura'],atmosphere=r['Condiciones atmosféricas'],notes=r['Observaciones'],raw_opportunity_rows_json=enc([x['_raw'] for x in rows]),source_02_locators=enc([x['_locator'] for x in rows]),source_03_locators=enc([x['_locator'] for x in cr]),completion_evidence='NATIVE_SE_CENSA_SI; PARTIAL_NOTES_RETAINED' if survey else 'NOT_SURVEY_QUALIFIED',coverage_completeness='NOT_INDEPENDENTLY_MEASURED',reporting_contract='PRESENCE_ONLY_JOIN_SURVEYED_CHILD; CONDITIONAL_NONRECORD_NOT_TRUE_ABSENCE')
  values={};states={}
  for tx in TAXA:
   pp=bytax.get(tx,[])
   state='SOURCE_CONTEXT_AMBIGUITY' if len(contexts)!=1 else 'SOURCE_CONFLICT' if flags!={'Sí'} and pp else 'UNSURVEYED' if flags!={'Sí'} else 'SOURCE_COUNT_INVALID' if bad or dupnum else 'SURVEYED_POSITIVE' if pp else 'SURVEYED_CONDITIONAL_NONDETECTION'
   val=sum(parsed.get(tx,[])) if eligible and pp else 0 if eligible else None
   values[tx]=val;states[tx]=state
   typed.append(dict(opportunity_uid=oid,taxon=tx,typed_state=state,count=val,native_count_rows=len(pp),native_count_values_json=enc([x['Individuos'] for x in pp]),source_03_locators=enc([x['_locator'] for x in pp])))
  base['focal_positive_species']=sum(v is not None and v>0 for v in values.values());base['focal_conditional_nonrecords']=sum(s=='SURVEYED_CONDITIONAL_NONDETECTION' for s in states.values())
  audit.append(base)
  if eligible:visits.append(dict(base,values=values,states=states))
  if survey and watercode not in range(6):unknown.append(dict(base,all_taxa_raw_rows_json=enc([x['_raw'] for x in cr]),focal_counts_json=enc(values),focal_states_json=enc(states)))
  if reason!='ELIGIBLE_BIRD_ONLY' or date_state not in ('MATCH','BLANK') or dupnum or bad:exceptions.append(dict(base,invalid_count_locators=enc(bad)))
  if len(rows)>1 or dupnum:duplicates.append(dict(base))
 for k,rr in counts.items():
  if k not in opp:exceptions.append(dict(exclusion_reason='ORPHAN_POSITIVE',native_locality_key_json=enc(list(k)),source_03_locators=enc([r['_locator'] for r in rr])))
 write('NATIVE_SOURCE_SCHEMAS.csv',schemas);write('README_CONTRACTS.csv',contracts)
 write('NATIVE_TYPED_SPECIES_STATES.csv',typed);write('SOURCE_EXCEPTIONS.csv',exceptions)
 write('DUPLICATE_CONTEXTS.csv',duplicates,['opportunity_uid','census_id','native_row_count','context_variants','exact_duplicate_count_rows'] if not duplicates else None)
 assert not any(r.get('exclusion_reason') in ('ORPHAN_POSITIVE','CONTEXT_AMBIGUITY','DATE_OR_COUNT_INVALID') for r in exceptions), 'QUALIFICATION_FAILURE'
 assert all(r['census_actual_date_state']=='MATCH' for r in visits),'ACTUAL_DATE_MISMATCH_REQUIRES_EXPLICIT_SCOPE'
 assert all(not r['invalid_count_rows'] and not r['exact_duplicate_count_rows'] for r in audit),'COUNT_FAILURE'
 partial_positions={r['position'] for r in visits if r['opportunity_uid'] in PARTIAL}
 assert len(partial_positions)==3 and {r['opportunity_uid'] for r in visits if r['opportunity_uid'] in PARTIAL}==PARTIAL
 def panel(vv,omit=set()):
  slots=defaultdict(list)
  for r in vv:slots[r['year'],r['position']].append(r)
  posyears=defaultdict(set)
  for y,p in slots:posyears[p].add(y)
  complete={p for p,yy in posyears.items() if yy==YEARS}-omit
  out=[]
  for (y,p),rr in sorted(slots.items()):
   if p not in complete:continue
   assert len({z['parent_id'] for z in rr})==1
   values={s:sum(F(z['values'][s]) for z in rr)/len(rr) for s in TAXA}
   out.append(dict(year=y,position=p,child_id=rr[0]['child_id'],parent_id=rr[0]['parent_id'],month=rr[0]['month'],visit_n=len(rr),visit_ids=enc(sorted(z['opportunity_uid'] for z in rr)),actual_dates=enc(sorted(z['actual_date'] for z in rr)),values=values))
  return out,complete,posyears,slots
 panels={};support=[];member=[]
 for config,known,omit in [('G0',True,set()),('G1',True,partial_positions),('G2',False,set()),('G3',False,partial_positions)]:
  vv=[r for r in visits if not known or r['known_water_eligible']];ss,pp,py,allslots=panel(vv,omit);panels[config]=ss
  write(config+'_SLOTS.csv',[dict({k:v for k,v in r.items() if k!='values'},**{s:float(v) for s,v in r['values'].items()}) for r in ss])
  write(config+'_SLOT_EXACT_VALUES.csv',[dict(year=r['year'],position=r['position'],species=s,count_exact=str(v),typed_state='POSITIVE_SLOT_MEAN' if v>0 else 'QUALIFIED_ZERO_SLOT_MEAN',visit_n=r['visit_n']) for r in ss for s,v in r['values'].items()])
  support.append(dict(configuration=config,qualified_native_visits=len(vv),positions=len(pp),slots=len(ss),children=len({r['child_id'] for r in ss}),parents=len({r['parent_id'] for r in ss}),visit_multiplicity=enc(Counter(r['visit_n'] for r in ss)),years=enc(Counter(r['year'] for r in ss)),months=enc(Counter(r['month'] for r in ss))))
  member.extend(dict(configuration=config,position=p,years=enc(sorted(yy)),n_years=len(yy),complete_before_partial_omission=yy==YEARS,symmetrically_omitted=p in omit,retained=p in pp) for p,yy in sorted(py.items()))
  for r in audit:r[config+'_fixed_panel_member']=r['position'] in pp and r['bird_eligible'] and (not known or r['known_water_eligible'])
 write('NATIVE_OPPORTUNITY_ELIGIBILITY.csv',audit);write('PANEL_SUPPORT.csv',support);write('POSITION_MEMBERSHIP.csv',member)
 for u in unknown:
  for config in ('G0','G2'):
   ss=[r for r in panels[config] if r['year']==u['year'] and r['position']==u['position']]
   u[config+'_slot_count']=len(ss);u[config+'_visit_ids']=ss[0]['visit_ids'] if ss else '';u[config+'_slot_visits']=ss[0]['visit_n'] if ss else 0
  allsame=[r for r in visits if r['year']==u['year'] and r['position']==u['position']]
  u['all_bird_eligible_same_slot_visits']=len(allsame)
  u['existing_known_water_same_slot_visits']=sum(r['known_water_eligible'] for r in allsame)
 write('SEVEN_UNKNOWN_SOURCE_EVIDENCE.csv',unknown)
 write('QUALIFIED_VISITS_COUNTS.csv',[dict({k:r[k] for k in ['opportunity_uid','actual_date','year','month','child_id','parent_id','position','known_water_eligible']},**r['values']) for r in visits])

 jout('RAW_RECOVERY_SUMMARY.json',dict(native_opportunities=len(audit),qualified_visits=len(visits),panels=support,partial_positions=sorted(partial_positions)))
 jout('RAW_INPUT_HASHES.json',INPUTS)
 print(enc(support))
if __name__=='__main__':main()
