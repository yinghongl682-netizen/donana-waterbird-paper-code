from runtime_config import OUTPUT
import csv
BR=OUTPUT/'bridge'
table1=[['Study feature','Aerial waterbird censuses','Terrestrial non-passerine-bird censuses'],['Period','April 2013–June 2023','January 2013–December 2023'],['Observation unit','Species count per eligible PNC or SB sector census','Species count per eligible visit; mean across visits within a year-specific locality–month slot'],['Support','75 PNC and 113 SB events; departure support 75/112; 75 shared events','702 fixed positions, 90 children, 30 parents; 7,722 slots, early/late 3,510/4,212'],['Primary role','Seasonal profiles and event-relative interspecific temporal correspondence','Components, seasonal/local signed changes and locality distributions within the same early/late periods'],['Near-date comparison','Partial historical named-locality ground subset, not an equal aerial footprint','Complete ±14-day rosters for 62 PNC and 78 SB events; seven-day support 35/55; same-day 1/0'],['Sensitivity','Year-balanced adjustment, within-year centring, retained-year/reference checks','699-position reduced frame, eleven whole-year omissions and early cutoffs 2016/2018']]
with (BR/'results/ground/BASELINE_PERIOD_COMPONENTS.csv').open(encoding='utf-8-sig') as f:a=[r for r in csv.DictReader(f) if r['window']=='ANNUAL']
ta=[['Species','f early','f late','q early','q late','μ early','μ late']];tb=[['Species','Δμ','Cf','Cq']]
for r in a:
 ta.append([r['species']]+[f'{float(r[k]):.3f}' for k in ['early_f','late_f','early_q','late_q','early_mu','late_mu']]);tb.append([r['species']]+[f'{float(r[k]):+.3f}' for k in ['delta_mu','Cf','Cq']])
O=OUTPUT/'tables';O.mkdir(parents=True,exist_ok=True)
for n,rows in [('Table1',table1),('Table2A',ta),('Table2B',tb)]:
 with (O/(n+'_R2_EXACT_DISPLAY.csv')).open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(rows)
