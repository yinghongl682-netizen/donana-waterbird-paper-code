"""Explicit public read-only acquisition using the final production WMS request.

Never called implicitly. Changed future responses remain unqualified and cannot
replace the exact approved 2026-11-08 snapshot merely by changing a hash guard.
"""
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import urlencode
from datetime import datetime,timezone
import argparse,json,hashlib
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-root',type=Path,required=True)
    a=p.parse_args();out=a.output_root.resolve();repo=Path(__file__).resolve().parents[3]
    if out.exists() or out.is_relative_to(repo):p.error('Use a new external directory')
    params=dict(SERVICE='WMS',VERSION='1.1.1',REQUEST='GetFeatureInfo',LAYERS='Parcelas_Censo_Aereo_desde_2013',QUERY_LAYERS='Parcelas_Censo_Aereo_desde_2013',SRS='EPSG:25829',BBOX='721000,4077000,762000,4126000',WIDTH=1000,HEIGHT=1000,X=500,Y=500,INFO_FORMAT='application/json',FEATURE_COUNT=1000,buffer=1000)
    url='https://geoserver.icts-donana.es/geoserver/Seguimiento/wms?'+urlencode(params)
    with urlopen(Request(url,headers={'User-Agent':'Donana-reference-geography-reproduction'}),timeout=90) as response:
        body=response.read(10_000_001);status=response.status;content_type=response.headers.get('Content-Type')
    if len(body)>10_000_000:raise ValueError('Unexpected response size')
    out.mkdir(parents=True);(out/'whole_buffer1000.geojson').write_bytes(body)
    digest=hashlib.sha256(body).hexdigest();contract=json.loads((repo/'data/schema/fig1_final_contract.json').read_text('utf-8'))
    receipt=dict(url=url,retrieved_utc=datetime.now(timezone.utc).isoformat(),status=status,content_type=content_type,bytes=len(body),sha256=digest,qualified_snapshot=digest==contract['raw_wms_sha256'])
    (out/'HTTP_RECEIPT.json').write_text(json.dumps(receipt,indent=2),'utf-8')
    if not receipt['qualified_snapshot']:raise ValueError('Response retained but not qualified for final reproduction; inspect rather than weaken the guard')
    print(json.dumps(receipt))
if __name__=='__main__':main()
