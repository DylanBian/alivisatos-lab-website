"""Audit saved publication data against primary Crossref metadata. Does not publish."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import csv,json,re,unicodedata,difflib
from lxml import html

ROOT=Path(__file__).resolve().parent;REPORTS=ROOT/'reports'
rows=list(csv.DictReader((ROOT/'data/publications.csv').open()))
def fetch(url):
    with urlopen(Request(url,headers={'User-Agent':'Alivisatos-Website-Metadata-Audit/1.0'}),timeout=30) as response:return json.load(response)
cache=REPORTS/'crossref-response.json'
if not cache.exists():
    cache.write_text(json.dumps(fetch('https://api.crossref.org/works?query.author=Alivisatos&rows=1000&select=DOI,title,published,container-title,volume,issue,page')))
index={r['DOI'].lower():r for r in json.loads(cache.read_text())['message']['items']}
supplement_path=REPORTS/'crossref-supplement.json'
existing_supplement=json.loads(supplement_path.read_text()) if supplement_path.exists() else []
index.update({r['DOI'].lower():r for r in existing_supplement})
dois={unquote(r['url'].split('doi.org/')[1]).lower() for r in rows if 'doi.org/' in r['url']}
def resolve(doi):
    try:return doi,fetch('https://api.crossref.org/works/'+quote(doi,safe=''))['message'],None
    except HTTPError as error:return doi,None,'http_'+str(error.code)
    except Exception as error:return doi,None,type(error).__name__
supplement=list(existing_supplement);errors={}
with ThreadPoolExecutor(max_workers=3) as pool:
    for doi,item,error in pool.map(resolve,sorted(dois-set(index))):
        if item:index[doi]=item;supplement.append(item)
        else:errors[doi]=error
(REPORTS/'crossref-supplement.json').write_text(json.dumps(supplement,ensure_ascii=False,indent=2))
def plain(markup):return html.fragment_fromstring(markup,create_parent='div').text_content()
def normalized(text):return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',re.sub(r'<[^>]+>','',text)).encode('ascii','ignore').decode().lower())
report=[]
for r in rows:
    if r['kind']!='publication':continue
    doi=unquote(r['url'].split('doi.org/')[1]) if 'doi.org/' in r['url'] else ''
    item=index.get(doi.lower())
    title=plain(r['title_html'])
    cross_title=(item.get('title') or [''])[0] if item else ''
    dates=(item.get('published-print') or item.get('published') or {}).get('date-parts',[[]])[0] if item else []
    year=str(dates[0]) if dates else ''
    ratio=difflib.SequenceMatcher(None,normalized(title),normalized(cross_title)).ratio() if item else 0
    year_match=(r['group']==year or (r['group']=='1980s' and year.startswith('198')))
    flag=('match' if year_match and ratio>=.9 else 'review') if item else ('missing_doi' if not doi else errors.get(doi.lower(),'not_found'))
    report.append(dict(record_id=r['id'],DOI=doi,page_year=r['group'],Crossref_year=year,page_title=title,Crossref_title=cross_title,match_flag=flag,title_similarity=round(ratio,3),Crossref_journal='; '.join(item.get('container-title',[])) if item else '',Crossref_volume=item.get('volume','') if item else '',Crossref_issue=item.get('issue','') if item else '',Crossref_page=item.get('page','') if item else ''))
with (REPORTS/'doi_check.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(report[0]));writer.writeheader();writer.writerows(report)
print('Audited',len(report),'regular records;',sum(r['match_flag']=='match' for r in report),'automatic matches;',sum(r['match_flag']!='match' for r in report),'review flags.')
for r in report:
    if r['match_flag']!='match':print(r['record_id'],r['page_year'],r['Crossref_year'],r['match_flag'],r['DOI'],r['page_title'][:75])
