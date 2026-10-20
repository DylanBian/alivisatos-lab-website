"""Apply reviewed metadata corrections to local data only. Never publishes."""
from pathlib import Path
from urllib.parse import unquote,quote
from html import escape
import csv,json,re,shutil

ROOT=Path(__file__).resolve().parent
path=ROOT/'data/publications.csv'
backup=ROOT/'backup/2026-10-20/publications-data-pre-audit.csv'
if not backup.exists():shutil.copy2(path,backup)
rows=list(csv.DictReader(path.open()))
items=json.loads((ROOT/'reports/crossref-response.json').read_text())['message']['items']
items+=json.loads((ROOT/'reports/crossref-supplement.json').read_text())
items+=json.loads((ROOT/'reports/crossref-title-queries.json').read_text())['p0479']
index={i['DOI'].lower():i for i in items}
fixes={
'p0280':'10.1126/science.1172104',
'p0297':'10.1021/nl801817d',
'p0331':'10.1038/nbt1100',
'p0347':'10.1126/science.1096566',
'p0383':'10.1002/1521-4095(20020618)14:12<882::AID-ADMA882>3.0.CO;2-Y',
'p0386':'10.1023/A:1021175612112',
'p0399':'10.1126/science.1058495',
'p0400':'10.1002/1438-5171(200112)2:4<261::AID-SIMO261>3.0.CO;2-P',
'p0428':'10.1103/PhysRevB.59.R10421',
'p0433':'10.1126/science.281.5385.2013',
'p0479':'10.1016/0009-2614(92)80023-5',
}
def initials(given):
    return ' '.join('-'.join(part[0]+'.' for part in token.split('-') if part) for token in re.findall(r'[\w]+(?:-[\w]+)*',given,flags=re.U))
def authors(item):
    parts=[]
    for author in item.get('author',[]):
        family=author.get('family','');given=author.get('given','')
        if family:
            text=family+(', '+initials(given) if given else '')
            if author.get('suffix'):text+=', '+author['suffix']
        else:text=author.get('name','')
        if text:parts.append(text)
    return escape('; '.join(parts))
changes=[]
for row in rows:
    before=dict(row)
    if row['id'] in fixes:
        doi=fixes[row['id']]
        assert doi.lower() in index,doi
        row['url']='https://doi.org/'+quote(doi,safe='/()')
        row['link_label']=doi
    doi=unquote(row['url'].split('doi.org/')[1]).lower() if 'doi.org/' in row['url'] else ''
    item=index.get(doi)
    if item:
        dates=(item.get('published-print') or item.get('published') or {}).get('date-parts',[[]])[0]
        year=str(dates[0]) if dates else ''
        if row['kind']=='publication' and year:
            row['group']='1980s' if year.startswith('198') else year
            row['year']=year
        a=authors(item)
        if a:row['authors_html']=a
        if row['id']=='p0297':row['details_html']='8 (8), 2551–2555'
        if row['id'] in ('p0172','p0196'):row['title_html']=escape(item['title'][0])
    title=row['title_html']
    for formula,markup in {
      'Cs2AgInCl6':'Cs<sub>2</sub>AgInCl<sub>6</sub>','Cs2AgSbCl6':'Cs<sub>2</sub>AgSbCl<sub>6</sub>',
      'CsPbBr3':'CsPbBr<sub>3</sub>','CsPbX3':'CsPbX<sub>3</sub>','CaF2':'CaF<sub>2</sub>',
      'Cu3As':'Cu<sub>3</sub>As','FeS2':'FeS<sub>2</sub>','NaLnF4':'NaLnF<sub>4</sub>',
      'Bi2S3':'Bi<sub>2</sub>S<sub>3</sub>','PbSxSe1-x':'PbS<sub>x</sub>Se<sub>1-x</sub>',
    }.items():title=title.replace(formula,markup)
    subs=str.maketrans('₀₁₂₃₄₅₆₇₈₉','0123456789')
    row['title_html']=re.sub('[₀₁₂₃₄₅₆₇₈₉]+',lambda m:'<sub>'+m.group().translate(subs)+'</sub>',title)
    for key,value in row.items():
        if value!=before[key]:changes.append(dict(record_id=row['id'],field=key,before=before[key],after=value,source_doi=doi))
with path.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (ROOT/'reports/bibliographic-corrections.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['record_id','field','before','after','source_doi']);w.writeheader();w.writerows(changes)
print('Reviewed DOI corrections:',len(fixes),'; changed fields:',len(changes),'; refiled records:',sum(c['field']=='group' for c in changes))
