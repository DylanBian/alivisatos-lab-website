"""Verify anonymous plain URLs, without query strings, cookies, or auth headers."""
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from pathlib import Path
import argparse,re,json,datetime

PAGES=['','positions/','members/','alumni/','research/','publications/','news/','gallery/']
FORBIDDEN=['Kamran','Forghani','kforghani','Join the Group','Open Positions','/positions','website is new','binyuwu AT','Binyuwu AT']
def verify(base,slug):
    url=base.rstrip('/')+'/'+slug
    try:
        with urlopen(Request(url,headers={'User-Agent':'Alivisatos-Public-Page-Verification/1.0'}),timeout=35) as response:
            status=response.status;body=response.read().decode('utf-8','replace')
    except HTTPError as error:status=error.code;body=error.read().decode('utf-8','replace')
    except Exception as error:return dict(path='/'+slug,status='error',result='FAIL',detail=type(error).__name__,url=url)
    hits=[term for term in FORBIDDEN if term.lower() in body.lower()]
    success=(status==404 if slug=='positions/' else status==200 and not hits)
    detail=', '.join(hits) if hits else ('expected 404' if slug=='positions/' and status!=404 else '')
    return dict(path='/'+slug,status=status,result='PASS' if success else 'FAIL',detail=detail,url=url)
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='https://alivisatoslab.uchicago.edu');args=parser.parse_args()
    if '?' in args.base:parser.error('Plain URLs only')
    rows=list(ThreadPoolExecutor(max_workers=3).map(lambda slug:verify(args.base,slug),PAGES))
    lines=['| Plain URL | HTTP | Result | Details |','|---|---:|---|---|']
    lines += [f'| {r["path"]} | {r["status"]} | {r["result"]} | {r["detail"] or "—"} |' for r in rows]
    report='\n'.join(lines);print(report)
    root=Path(__file__).resolve().parents[1]
    (root/'reports/public-verification.json').write_text(json.dumps(rows,indent=2))
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with (root/'CHANGELOG.md').open('a') as f:f.write('\n\n## Anonymous plain-URL check '+stamp+'\n\nBase: '+args.base+'\n\n'+report+'\n')
    raise SystemExit(0 if all(r['result']=='PASS' for r in rows) else 1)
if __name__=='__main__':main()
