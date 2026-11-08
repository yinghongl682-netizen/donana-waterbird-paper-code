"""Validate actual external figure interfaces without pretending to restore raw data."""
from pathlib import Path
import csv,json,hashlib
def validate_run(root,figures=('Fig2','Fig3','Fig4','Fig5')):
    root=Path(root).resolve(strict=True)
    contract=json.loads((Path(__file__).resolve().parents[2]/'data/schema/figures_2_5_contract.json').read_text('utf-8'))
    result={'scope':contract['scope'],'files':[]}
    for figure in figures:
        for item in contract['figures'][figure]:
            path=root/item['path']
            if not path.is_file() or path.stat().st_size==0:raise ValueError('Missing/empty '+figure+' input: '+item['path'])
            rec={'figure':figure,'relative_path':item['path'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}
            if item['format']=='csv':
                with path.open(encoding='utf-8-sig',newline='') as f:
                    reader=csv.DictReader(f)
                    if reader.fieldnames!=item['columns']:raise ValueError('Unexpected columns: '+item['path'])
                    count=0
                    for row in reader:
                        if None in row or any(v is None for v in row.values()):raise ValueError('Malformed row: '+item['path'])
                        count+=1
                    if count==0:raise ValueError('Empty source table: '+item['path'])
                    rec['rows']=count
            result['files'].append(rec)
    result['status']='INTERFACES_VALIDATED_NATIVE_SCIENTIFIC_LOCKS_STILL_REQUIRED'
    return result
