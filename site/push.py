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
MAX_RAW_CHARS=850_000

def replace_module(raw, fragment, marker, css=None):
    """Replace the AUTO module content; when css is given, also store it as the module's Free-Form CSS."""
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
        before=json.loads(m.group(2))
        found=hits;after=walk(before)
        if hits==found:return m.group(0)
        if css is not None:
            after.setdefault('css',{}).setdefault('desktop',{}).setdefault('value',{})['freeForm']=css
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
            # Idempotent: already-corrected labels are left alone.
            value=re.sub(r'(?<!Nat\.) Synth</em>',' Nat. Synth</em>',value)
            value=re.sub(r'(?<!Sci\. )(?<![A-Za-z])Adv\.</em>','Sci. Adv.</em>',value)
            value=value.replace('J. Am. Chem. Soc</em>. 2023','J. Am. Chem. Soc.</em> 2023')
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

RESEARCH_AREA_DOI={'10.1021/acs.accounts.4c00708':'synthesis','10.1021/acsnano.5c07437':'lctem',
                   '10.1038/s41467-025-60848-5':'spectroscopy','10.1021/acsnano.4c04083':'quantum'}
RESEARCH_AREA_LABEL={'synthesis':'Synthesis and Properties','lctem':'Electron Microscopy in Liquid',
                     'spectroscopy':'Spectroscopy and Structure','quantum':'Quantum Information Science'}

def add_research_links(raw,counts):
    """After each area's selected-publication list on the Research page, link to that area's filtered publication list.

    The area is identified by the first DOI in the Divi text block. Idempotent: the link sits between AUTO markers.
    """
    def link(area):
        start=f'<!-- AUTO:research-more-{area}:START -->';end=f'<!-- AUTO:research-more-{area}:END -->'
        n=counts.get(area,0)
        return (f'{start}<p><a href="https://alivisatoslab.uchicago.edu/publications/#f-{area}"><strong>'
                f'All {n} group papers tagged {RESEARCH_AREA_LABEL[area]} →</strong></a></p>{end}')
    def walk(value):
        if isinstance(value,str):
            m=re.search(r'doi\.org/(10\.[^"<\s]+)',value)
            area=RESEARCH_AREA_DOI.get(m.group(1).lower()) if m else None
            if not area or not counts.get(area) or '</ul>' not in value: return value
            start=f'<!-- AUTO:research-more-{area}:START -->';end=f'<!-- AUTO:research-more-{area}:END -->'
            if start in value and end in value:
                return value[:value.index(start)]+link(area)+value[value.index(end)+len(end):]
            i=value.rindex('</ul>')+len('</ul>')
            return value[:i]+link(area)+value[i:]
        if isinstance(value,dict): return {k:walk(v) for k,v in value.items()}
        if isinstance(value,list): return [walk(v) for v in value]
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

def research_update(raw):
    counts_path=ROOT/'build'/'research-links.json'
    counts=json.loads(counts_path.read_text()) if counts_path.exists() else {}
    return add_research_links(replace_research_citations(raw),counts)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('page',choices=PAGE_IDS)
    parser.add_argument('--snapshot',type=Path,help='Offline raw HTML snapshot; no network')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if args.snapshot and args.apply:parser.error('Offline mode cannot publish')
    page=args.page;marker='home-updates' if page=='home' else page
    fragment=(ROOT/'build'/('research-content.raw' if page=='research' else f'{page}.html')).read_text()
    css=None
    if page!='research':
        fragment=fragment.strip()
        css_path=ROOT/'build'/f'{page}.css'
        css=css_path.read_text().strip() if css_path.exists() else None
    if args.snapshot:
        raw=args.snapshot.read_text();saved={'id':PAGE_IDS[page],'content':{'raw':raw}}
    else:
        base=os.environ.get('WP_BASE_URL','https://voices.uchicago.edu/alivisatosgroup').rstrip('/')
        if base not in ('https://voices.uchicago.edu/alivisatosgroup','https://alivisatoslab.uchicago.edu'):
            raise ValueError('Unexpected destination site')
        auth=base64.b64encode((os.environ['WP_USER']+':'+os.environ['WP_APP_PASSWORD']).encode()).decode()
        endpoint=base+'/wp-json/wp/v2/pages/'+str(PAGE_IDS[page])
        def request(url,payload=None):
            headers={'Authorization':'Basic '+auth,'Content-Type':'application/json','User-Agent':'alivisatos-site-maintenance/1.0','Accept':'application/json'}
            # The site returns occasional 503s; retry reads only. A failed write is never retried blindly.
            for attempt in range(4):
                req=Request(url,data=json.dumps(payload).encode() if payload is not None else None,headers=headers)
                try:
                    with urlopen(req,timeout=60) as response:return json.load(response)
                except (ConnectionError,TimeoutError) as error:
                    if payload is None and attempt<3:
                        time.sleep(5*(attempt+1));continue
                    raise
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
            # Journal-label corrections and the links to each area's publication list, applied to the live content.
            updated=research_update(raw)
            if updated==raw:
                print('Research: already up to date; nothing to publish.')
                if os.environ.get('GITHUB_ACTIONS'): print('::notice title=push research::Already up to date; nothing to publish.')
    else:
        updated=replace_module(raw,fragment,marker,css)
        if page=='members':
            updated,removed=remove_empty_sections(updated)
            print(f'Empty Divi sections removed: {len(removed)}',removed)
            if os.environ.get('GITHUB_ACTIONS'): print(f'::notice title=members sections::Empty Divi sections removed: {len(removed)} {removed}')
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=ROOT/'backup'/stamp;backup.mkdir(parents=True)
    (backup/f'{page}.json').write_text(json.dumps(saved,ensure_ascii=False,indent=2))
    diff=''.join(difflib.unified_diff(raw.splitlines(True),updated.splitlines(True),fromfile='current',tofile='generated'))
    (ROOT/'reports'/f'{page}.diff').write_text(diff)
    print('Saved backup and diff. Current SHA256:',hashlib.sha256(raw.encode()).hexdigest())
    if os.environ.get('GITHUB_ACTIONS') and not args.apply: print(f'::notice title=push {page}::live modified {saved.get("modified_gmt","?")}; raw {len(raw)} chars -> {len(updated)} chars; dry run')
    # 2026-10-20: a 1,074,426-char save came back empty (PHP regex backtrack limit is 1,000,000); 879,405 chars saved fine.
    if len(updated)>MAX_RAW_CHARS:
        message=f'{page}: generated page is {len(updated)} chars, above the {MAX_RAW_CHARS} limit; WordPress may save it empty. Nothing written.'
        if os.environ.get('GITHUB_ACTIONS'): print(f'::error title=push {page} too large::{message}')
        sys.exit(message)
    if not args.apply:
        print('Dry run only. Review reports/'+page+'.diff before using --apply.');return
    if request(endpoint+'?context=edit')['content']['raw']!=raw:
        raise RuntimeError('Page changed after the backup; no write performed')
    request(endpoint,{'content':updated})
    actual=request(endpoint+'?context=edit')['content']['raw']
    if page!='research' and (f'AUTO:{marker}:START' not in actual or len(actual)<0.5*len(updated)):
        # The save lost the module (seen 2026-10-20: page saved empty). Put the previous content back at once.
        request(endpoint,{'content':raw})
        back=request(endpoint+'?context=edit')['content']['raw']
        raise RuntimeError(f'Saved page lost the AUTO module ({len(actual)} chars saved). Previous content written back: '
                           f'{"identical" if back==raw else "DIFFERS, restore from revisions"}.')
    # Read the saved module back. WordPress may strip unsupported markup.
    roundtrip=actual if page=='research' else replace_module(actual,fragment,marker,css)
    if roundtrip!=actual:
        raise RuntimeError('Saved markup differs from generated fragment. Backup retained; inspect before further writes.')
    print('Published and verified saved Divi module. Check the public page visually as well.')
    if os.environ.get('GITHUB_ACTIONS'): print(f'::notice title=push {page}::published; read-back matches the build; raw {len(raw)} -> {len(actual)} chars')
    if page=='research':(ROOT/'build/research-content.before-c.raw').write_text(actual)
    # The public plain-URL check runs as a separate workflow step (scripts/verify_public.py at the repo root).

if __name__=='__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:
        if os.environ.get('GITHUB_ACTIONS'):
            page=sys.argv[1] if len(sys.argv)>1 else '?'
            message=f'{type(error).__name__}: {error}'.replace('%','%25').replace('\n','%0A')[:900]
            print(f'::error title=push {page}::{message}')
        raise
