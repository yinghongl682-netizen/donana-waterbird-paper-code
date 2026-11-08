"""Explicit input/output contract. No archive discovery or home-directory defaults."""
from pathlib import Path
import os,json
INPUT=Path(os.environ['DONANA_INPUT_ROOT']).resolve()
OUTPUT=Path(os.environ['DONANA_OUTPUT_ROOT']).resolve()
def ground_opportunities(path):
 import pandas as pd
 a=pd.read_csv(path,keep_default_na=False)
 rows=[]
 for r in a.to_dict('records'):
  key=json.loads(r['native_locality_key_json'])
  rows.append(dict(opportunity_uid=r['opportunity_uid'],Censo=r['census_id'],**{f'Localidad nivel {i}':key[i-1] for i in range(1,5)},**{'Se censa':'Sí' if str(r['survey_qualified'])=='True' else 'No'},surveyed_qualified=str(r['survey_qualified'])=='True',opportunity_source_locators_json=r['source_02_locators']))
 return pd.DataFrame(rows)
