"""Source qualification and original M9 summaries; private inputs stay external."""
from runtime_config import INPUT,OUTPUT
from hmb1_original_blocks import reconstruct
from m9_original_blocks import calculate,SPECIES
from pathlib import Path
import csv,pandas as pd
out=OUTPUT/'aerial';out.mkdir(parents=True,exist_ok=True)
with (INPUT/'contracts/aerial_taxon_set.csv').open(encoding='utf-8-sig',newline='') as f:taxa=list(csv.DictReader(f))
rows=reconstruct(INPUT/'raw_aerial.zip',out/'raw_rebuild',taxa)
# Existing Stage6C bird-only qualification predicate and wide-construction block.
species=SPECIES
a1=[r for r in rows if '2013-04'<=r['calendar_year_month']<='2023-06' and r['sector_code'] in ['PNC','SB'] and r['taxon'] in species and r['support_state'].startswith('ELIGIBLE_')]
from decimal import Decimal
wide={}
for r in a1:
 k=(r['archive_event_id'],r['sector_code']);d=wide.setdefault(k,{'unit':k[0],'parent_id':k[1],'actual_date':r['actual_census_date'],'year':int(r['actual_census_date'][:4]),'month':int(r['actual_census_date'][5:7])})
 assert r['taxon'] not in d;v=Decimal(r['recorded_count']);assert v.is_finite() and v>=0 and v==v.to_integral_value();d[r['taxon']]=int(v)
assert all(set(d)=={'unit','parent_id','actual_date','year','month',*species} for d in wide.values())
a=pd.DataFrame(sorted(wide.values(),key=lambda r:(r['actual_date'],r['parent_id'])),columns=['unit','parent_id','actual_date','year','month',*species])
assert len(a)==188 and a.groupby('parent_id').size().to_dict()=={'PNC':75,'SB':113}
a.to_csv(out/'A1_WIDE_COUNTS.csv',index=False,encoding='utf-8-sig')
m=out/'m9';(m/'native_data').mkdir(parents=True,exist_ok=True);(m/'qa').mkdir(exist_ok=True)
calculate(a.melt(id_vars=['unit','parent_id','actual_date','year','month'],value_vars=SPECIES,var_name='species',value_name='y'),m,a)
print('A1 reconstructed from raw ZIP: 188 sector-events, 1692 species rows')
