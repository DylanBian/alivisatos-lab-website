"""Update one marked Divi module, preserving all other blocks and attributes.

Defaults to a diff. --apply is explicit. Credentials are read only from env.
"""
from pathlib import Path
import argparse, base64, datetime, difflib, hashlib, json, os, re, sys, time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent
PAGE_IDS={'publications':1147,'members':1153,'alumni':1120,'news':1179,'home':2,'research':1198}
BLOCK=re.compile(r'<!-- wp:(divi/[\w-]+) (\{[\s\S]*?\}) (/?)-->')

def replace_module(raw, fragment, marker):
    start=f'<!-- AUTO:{marker}:START -->';end=f'<!-- AUTO:{marker}:END -->'
    hits=0
    def walk(value):
        nonlocal hits
        if isinstance(value,str) and start in value and end in value:
            if value.count(start)!=1 or value.count(end)!=1:raise ValueError('Ambiguous markers')
            hits+=1
            return value[:value.index(start)]+fragment+value[value.index(end)+len(end):]
        if isinstance(value,dict):return {key:walk(item) for key,item in value.items()}
        if isinstance(value,list):return [walk(item) for item in value]
        return value
    def block(m):
        before=json.loads(m.group(2));after=walk(before)
        if before==after:return m.group(0)
        encoded=json.dumps(after,ensure_ascii=False,separators=(',',':'))
        for char,escaped in [('--',r'\u002d\u002d'),('<',r'\u003c'),('>',r'\u003e'),('&',r'\u0026')]:
            encoded=encoded.replace(char,escaped)
        return '<!-- wp:'+m.group(1)+' '+encoded+' '+m.group(3)+'-->'
    result=BLOCK.sub(block,raw)
    if hits!=1:raise ValueError(f'Expected one marked module, found {hits}')
    for m in BLOCK.finditer(result):json.loads(m.group(2))
    return result

SECTION=re.compile(r'<!-- wp:divi/section \{[\s\S]*?\} -->[\s\S]*?<!-- /wp:divi/section -->')
EMPTY_ALLOWED={'divi/section','divi/row','divi/column','divi/image'}

def remove_empty_sections(raw):
    """Drop Divi sections that hold only rows, columns and image modules without any image URL.

    These empty sections add Divi's default padding and leave a blank band (Members page, 2026-10-20).
    Sections containing an AUTO marker, any URL, or any other module are kept.
    """
    removed=[]
    def keep(match):
        chunk=match.group(0)
        names=set(re.findall(r'<!-- wp:(divi/[\w-]+)',chunk))
        if 'AUTO:' in chunk or 'http' in chunk or not names<=EMPTY_ALLOWED:
            return chunk
        removed.append(sorted(names))
        return ''
    result=SECTION.sub(keep,raw)
    for m in BLOCK.finditer(result):json.loads(m.group(2))
    return result,removed

def replace_research_citations(raw):
    """Make the reviewed Research citation edits while preserving every Divi block."""
    def walk(value):
        if isinstance(value,str):
            for before,after in [(' Synth</em>',' Nat. Synth</em>'),('Adv.</em>','Sci. Adv.</em>'),('J. Am. Chem. Soc</em>. 2023','J. Am. Chem. Soc.</em> 2023')]:
                value=value.replace(before,after)
            return value
        if isinstance(value,dict): return {key:walk(item) for key,item in value.items()}
        if isinstance(value,list): return [walk(item) for item in value]
        return value
    def block(match):
        before=json.loads(match.group(2));after=walk(before)
        if before==after:return match.group(0)
        encoded=json.dumps(after,ensure_ascii=False,separators=(',',':'))
        for char,escaped in [('--',r'\u002d\u002d'),('<',r'\u003c'),('>',r'\u003e'),('&',r'\u0026')]:encoded=encoded.replace(char,escaped)
        return '<!-- wp:'+match.group(1)+' '+encoded+' '+match.group(3)+'-->'
    updated=BLOCK.sub(block,raw)
    for match in BLOCK.finditer(updated):json.loads(match.group(2))
    return updated

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('page',choices=PAGE_IDS)
    parser.add_argument('--snapshot',type=Path,help='Offline raw HTML snapshot; no network')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if args.snapshot and args.apply:parser.error('Offline mode cannot publish')
    page=args.page;marker='home-updates' if page=='home' else page
    fragment=(ROOT/'build'/('research-content.raw' if page=='research' else f'{page}.html')).read_text()
    if page!='research':fragment=fragment.strip()
    if args.snapshot:
        raw=args.snapshot.read_text();saved={'id':PAGE_IDS[page],'content':{'raw':raw}}
    else:
        base=os.environ.get('WP_BASE_URL','https://voices.uchicago.edu/alivisatosgroup').rstrip('/')
        if base not in ('https://voices.uchicago.edu/alivisatosgroup','https://alivisatoslab.uchicago.edu'):
            raise ValueError('Unexpected destination site')
        auth=base64.b64encode((os.environ['WP_USER']+':'+os.environ['WP_APP_PASSWORD']).encode()).decode()
        endpoint=base+'/wp-json/wp/v2/pages/'+str(PAGE_IDS[page])
        def request(url,payload=None):
            headers={'Authorization':'Basic '+auth,'Content-Type':'application/json'}
            # The site returns occasional 503s; retry reads only. A failed write is never retried blindly.
            for attempt in range(4):
                req=Request(url,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
                try:
                    with urlopen(req,timeout=60) as response:return json.load(response)
                except HTTPError as error:
                    if payload is None and error.code in (502,503,504) and attempt<3:
                        time.sleep(5*(attempt+1));continue
                    if error.code in (401,403):
                        sys.exit(f'WordPress refused the request ({error.code}). Stop and report; check the Application Password.')
                    raise
        saved=request(endpoint+'?context=edit');raw=saved['content']['raw']
    if page=='research':
        if args.snapshot:
            updated=replace_research_citations(raw)
            if updated!=fragment:
                raise RuntimeError('Research snapshot differs from the generated target; review its source and diff.')
        else:
            baseline=ROOT/'build/research-content.before-c.raw'
            if not baseline.exists() or raw!=baseline.read_text():
                raise RuntimeError('Research page differs from the reviewed baseline; refresh and review before publishing.')
            updated=fragment
    else:
        updated=replace_module(raw,fragment,marker)
        if page=='members':
            updated,removed=remove_empty_sections(updated)
            print(f'Empty Divi sections removed: {len(removed)}',removed)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=ROOT/'backup'/stamp;backup.mkdir(parents=True)
    (backup/f'{page}.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2))
    diff=''.join(difflib.unified_diff(raw.splitlines(True),updated.splitlines(True),fromfile='current',tofile='generated'))
    (ROOT/'reports'/f'{page}.diff').write_text(diff)
    print('Saved backup and diff. Current SHA256:',hashlib.sha256(raw.encode()).hexdigest())
    if not args.apply:
        print('Dry run only. Review reports/'+page+'.diff before using --apply.');return
    if request(endpoint+'?context=edit')['content']['raw']!=raw:
        raise RuntimeError('Page changed after the backup; no write performed')
    request(endpoint,{'content':updated})
    actual=request(endpoint+'?context=edit')['content']['raw']
    # Read the saved module back. WordPress may strip unsupported markup.
    roundtrip=actual if page=='research' else replace_module(actual,fragment,marker)
    if roundtrip!=actual:
        raise RuntimeError('Saved markup differs from generated fragment. Backup retained; inspect before further writes.')
    print('Published and verified saved Divi module. Check the public page visually as well.')
    if page=='research':(ROOT/'build/research-content.before-c.raw').write_text(actual)
    # The public plain-URL check runs as a separate workflow step (scripts/verify_public.py at the repo root).

if __name__=='__main__':main()
