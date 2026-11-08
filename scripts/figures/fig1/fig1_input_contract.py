"""Fail-closed contract for the final externally supplied Fig. 1 inputs."""
from pathlib import Path
import csv, hashlib, json
REPO = Path(__file__).resolve().parents[3]
CONTRACT = REPO / 'data/schema/fig1_final_contract.json'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def validate_inputs(root, union):
    root=Path(root).resolve(strict=True);union=Path(union).resolve(strict=True)
    contract=json.loads(CONTRACT.read_text('utf-8'))
    for relative,expected in contract['files'].items():
        if sha(root/relative)!=expected:raise ValueError('Unqualified final input: '+relative)
    qa_path=root/'SENTINEL2_20220720_QA.json'
    image_qa=json.loads(qa_path.read_text('utf-8'))
    if not isinstance(image_qa.pop('created_utc',None),str):raise ValueError('Missing image processing timestamp')
    if image_qa!=contract['sentinel_qa_semantics']:raise ValueError('Sentinel processing metadata differs beyond timestamp')
    if sha(union)!=contract['union_sha256']:raise ValueError('Final WMS union identity mismatch')
    data=json.loads((root/'F1/support/plot_data/MAP_LAYERS_FINAL.json').read_text('utf-8'))
    if set(data)!={'extent','north','locator_point','F1_OFFICIAL_MAINLAND_MASK','F1_COAST','F1_RIVERS','world'}:
        raise ValueError('Minimal final map schema required; no event or legacy sector layer')
    with (root/'F1/support/plot_data/CALENDAR_396_LOCKED_STATES.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
    keys={(r['source'],int(r['year']),int(r['month'])) for r in rows}
    expected={(s,y,m) for s in ('PNC','SB','GROUND') for y in range(2013,2024) for m in range(1,13)}
    if len(rows)!=396 or keys!=expected or any(r['included'] not in ('0','1') for r in rows):raise ValueError('Expected all 396 unique locked binary observation states')
    return dict(status='VALIDATED_FINAL_INPUTS',files=contract['files'],sentinel_qa_sha256=sha(qa_path),sentinel_qa_semantics_equal=True,ignored_qa_field='created_utc only',union_sha256=sha(union),calendar_states=len(rows),included_by_source={s:sum(int(r['included']) for r in rows if r['source']==s) for s in ('PNC','SB','GROUND')},omitted_inputs=contract['omitted_inputs'],scope='Final display inputs; no new ecological estimate')
