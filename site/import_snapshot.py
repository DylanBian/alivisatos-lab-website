"""One-time import of the saved WordPress source; no network or site writes."""
from pathlib import Path
import csv, json, re, html as escaping
from lxml import html
import yaml

ROOT = Path(__file__).resolve().parent
BACKUP = ROOT / 'backup/2026-10-20'
for directory in ('data', 'templates', 'assets', 'build', 'reports'):
    (ROOT / directory).mkdir(exist_ok=True)

def module(name):
    raw = (BACKUP / (name + '.html')).read_text()
    for m in re.finditer(r'<!-- wp:divi/code (.*?) /-->', raw, re.S):
        data = json.loads(m.group(1))
        value = data.get('content', {}).get('innerContent', {}).get('desktop', {}).get('value', '')
        marker = 'home-updates' if name == 'home' else name
        if f'AUTO:{marker}:START' in value:
            return value
    raise ValueError('No marked code module: ' + name)

def inner(el):
    return (el.text or '') + ''.join(html.tostring(c, encoding='unicode', with_tail=True) for c in el)

def get(el, cls):
    result = el.xpath('.//*[contains(concat(" ",normalize-space(@class)," ")," '+cls+' ")]')
    return result[0] if result else None

def field(el, cls):
    found = get(el, cls)
    if found is None:return ''
    # Three historical spans were unclosed; nested metadata is a sibling field, not part of this one.
    return (found.text or '') if cls in ('ap-journal','ap-year-tag','ap-details') else inner(found)

source = module('publications')
root = html.fragment_fromstring(source, create_parent='div')
records = []
for i, el in enumerate(root.xpath('.//article')):
    selected = 'ap-selected-card' in el.get('class', '').split()
    parent = next((p for p in el.iterancestors('details')), None)
    year_group = parent.get('id').removeprefix('pub-') if parent is not None else ''
    a = get(el, 'ap-doi-link')
    extra = get(el, 'ap-card-meta')
    extra = html.fromstring(html.tostring(extra))
    for child in list(extra):
        if any(c in child.get('class','').split() for c in ('ap-journal','ap-year-tag','ap-details','ap-doi-link')):
            extra.remove(child)
    records.append(dict(id=f'p{i+1:04d}', kind='selected' if selected else 'publication', group=year_group,
        title_html=field(el,'ap-card-title'), authors_html=field(el,'ap-authors'),
        journal_html=field(el,'ap-journal'), journal_class=get(el,'ap-journal').get('class','ap-journal'),
        year=field(el,'ap-year-tag'), details_html=field(el,'ap-details'),
        url=a.get('href','') if a is not None else '', link_label=a.text_content() if a is not None else '',
        attributes=json.dumps(dict(el.attrib)), extra_meta_html=inner(extra)))
with (ROOT/'data/publications.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)
blocks=list(re.finditer(r'<details class="ap-year-toggle"[\s\S]*?</details>',source))
first=blocks[0].group(0)
year_template=first[:first.index('<article')]+'@@CARDS@@'+first[first.rindex('</article>')+10:]
(ROOT/'templates/publication-year.html').write_text(year_template.replace('2026','@@YEAR@@'))
source=source[:blocks[0].start()]+'@@YEARS@@'+source[blocks[-1].end():]
source=re.sub(r'<article class="ap-card ap-selected-card"[\s\S]*?</article>','@@SELECTED@@',source)
# Multiple selected placeholders deliberately collapse to a single insertion point.
source=source.replace('@@SELECTED@@','',11)
source=re.sub(r'<nav class="ap-nav"[\s\S]*?</nav>','@@NAV@@',source)
(ROOT/'templates/publications.html').write_text(source)

for name in ('members','alumni','news','home'):
    source=module(name); groups=[]
    # Each original article remains a rich HTML template, with commonly edited fields extracted.
    for i,m in reversed(list(enumerate(re.finditer(r'<article\b[\s\S]*?</article>',source)))):
        markup=m.group(0);el=html.fromstring(markup)
        headings=el.xpath('.//h3|.//h2');heading=headings[0] if headings else None
        title=inner(heading) if heading is not None else ''
        template=markup
        if title:template=template.replace('>'+title+'</'+heading.tag+'>','>@@TITLE_HTML@@</'+heading.tag+'>',1)
        images=el.xpath('.//img');image=images[0] if images else None
        values={'title_html':title}
        if image is not None:
            for key,attr in [('image_url','src'),('image_alt','alt')]:
                value=image.get(attr,'');values[key]=value
                template=template.replace(attr+'="'+escaping.escape(value,quote=True)+'"',attr+'="@@'+key.upper()+'@@"',1)
        groups.insert(0,dict(id=f'{name}-{i+1:03d}',**values,template_html=template))
        source=source[:m.start()]+'@@'+name.upper()+'-'+str(i+1)+'@@'+source[m.end():]
    (ROOT/'data'/f'{name}.yaml').write_text(yaml.safe_dump(groups,allow_unicode=True,sort_keys=False,width=110))
    (ROOT/'templates'/f'{name}.html').write_text(source)
print('Imported current live modules and structured publication records.')
