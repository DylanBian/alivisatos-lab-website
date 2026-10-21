"""Check the generated page sections against the data and the site rules. Run after build.py."""
from pathlib import Path
from collections import Counter
import json, re
from lxml import html
import yaml
from push import BLOCK, replace_module, replace_research_citations, MAX_RAW_CHARS

ROOT = Path(__file__).resolve().parent
PAGES = ('publications', 'members', 'alumni', 'news', 'home')
FORBIDDEN = ['Kamran', 'Forghani', 'kforghani', 'Join the Group', 'Open Positions', '/positions', 'website is new', 'binyuwu AT', 'sci-hub']

fragments = {n: (ROOT / 'build' / f'{n}.html').read_text() for n in PAGES}
styles = {n: (ROOT / 'build' / f'{n}.css').read_text() for n in PAGES}
roots = {n: html.fragment_fromstring(f, create_parent='div') for n, f in fragments.items()}


def classes(node):
    return set(node.get('class', '').split())


def by_class(root, cls, tag='*'):
    return root.xpath(f'.//{tag}[contains(concat(" ",normalize-space(@class)," ")," {cls} ")]')


for name, fragment in fragments.items():
    marker = 'home-updates' if name == 'home' else name
    stack = []
    for m, kind in re.findall(r'<!--\s*AUTO:([^:]+):(START|END)\s*-->', fragment):
        if kind == 'START':
            stack.append(m)
        else:
            assert stack and stack.pop() == m, f'{name}: unbalanced AUTO:{m}'
    assert not stack, f'{name}: unclosed AUTO markers'
    assert fragment.count(f'<!-- AUTO:{marker}:START -->') == 1 and fragment.count(f'<!-- AUTO:{marker}:END -->') == 1
    assert not roots[name].xpath('.//style|.//script|.//input|.//button'), f'{name}: elements that are removed on save'
    for word in FORBIDDEN:
        assert word.casefold() not in fragment.casefold(), f'{name}: forbidden text {word!r}'
    assert '>' not in styles[name], f'{name}: CSS contains ">"'
    assert styles[name].startswith('.ag-site-root'), f'{name}: CSS missing'
    for a in roots[name].xpath('.//a[starts-with(@href,"mailto:")]'):
        assert '@uchicago.edu' in a.get('href'), f'{name}: unexpected email {a.get("href")}'
    # every in-page filter link needs Divi's smooth-scroll opt-out, or Divi swallows the click
    for a in roots[name].xpath('.//a[starts-with(@href,"#")]'):
        assert 'et_smooth_scroll_disabled' in classes(a), f'{name}: in-page link without et_smooth_scroll_disabled: {a.get("href")}'
    # every filter chip points at a target that exists
    ids = set(roots[name].xpath('.//@id'))
    for a in by_class(roots[name], 'ag-site-chip', 'a'):
        assert a.get('href', '#')[1:] in ids, f'{name}: chip without target {a.get("href")}'
    encoded = json.dumps({'a': fragment, 'b': styles[name]}, ensure_ascii=False)
    assert len(encoded) * 1.2 < MAX_RAW_CHARS, f'{name}: module too large'
print('all pages: markers balanced; no removed elements; forbidden text absent; CSS has no ">"; filter chips resolve')

# Members
members = yaml.safe_load((ROOT / 'data/members.yaml').read_text())
mroot = roots['members']
cards = by_class(mroot, 'ag-site-member-card', 'article') + by_class(mroot, 'ag-site-pi', 'article')
assert len(cards) == len(members) == 20
assert not mroot.xpath('.//figure'), 'members: group photo banner removed (2026-10-20)'
mails = set(mroot.xpath('.//a[starts-with(@href,"mailto:")]/@href'))
assert len(mails) >= 19, 'members: personal emails kept plus lab contact'
assert 'mailto:alivisatos-lab@uchicago.edu' in mails
assert 'GCIS E247H'.replace('GCIS ', '') in fragments['members'] or 'E247H' in fragments['members']
for m in members:
    card = mroot.xpath(f'.//article[@id="{m["id"]}"]')[0]
    for r in m.get('research', []):
        assert f'https://alivisatoslab.uchicago.edu/research/#{r["area"]}' in card.xpath('.//a/@href')
yi = mroot.xpath('.//article[@id="members-006"]')[0]
assert 'AI for Science, Electron Microscopy' in yi.text_content() and 'research/#lctem' in ' '.join(yi.xpath('.//a/@href'))
ida = ' '.join(mroot.xpath('.//article[@id="members-012"]//a/@href'))
assert 'research/#synthesis' in ida and 'research/#spectroscopy' in ida
assert len(mroot.xpath('.//a[contains(@href,"scholar.google.com")]')) == sum(1 for m in members if m.get('scholar'))
print(f'members: {len(cards)} people; research links; emails; contact block; no banner')

# Alumni
alumni = yaml.safe_load((ROOT / 'data/alumni.yaml').read_text())
acards = by_class(roots['alumni'], 'ag-site-alumni-card', 'article')
assert len(alumni) == len(acards) == 187 and len({r['name'] for r in alumni}) == 187
assert sum(1 for c in acards if sum(x.startswith('ag-site-r-') for x in classes(c)) > 1) == 11  # Ophir Klein: undergraduate (Dylan, 2026-10-20)
segments = by_class(roots['alumni'], 'ag-site-sector-segment', 'span')
assert len(segments) == 3 and all(re.fullmatch(r'width:\d+\.\d\d%', s.get('style', '')) for s in segments)
assert ':target' in styles['alumni']
for r in alumni:
    if r.get('verified'):  # a confirmed position needs both the position page and the identity tie to the group
        assert str(r.get('source', '')).startswith('http') and str(r.get('identity', '')).startswith('http'), f'alumni: {r["name"]} verified without source and identity'
print('alumni: 187 cards (11 with two roles shown once); sector bar; sector and role filters; verified entries carry identity ties')

# News
news = yaml.safe_load((ROOT / 'data/news.yaml').read_text())
published = [n for n in news if n.get('publish', True)]
ncards = roots['news'].xpath('.//article')
assert len(published) == len(ncards) == 13
assert all(n.get('verified') and n.get('source_url', '').startswith('https://') for n in published)
assert 'Editors’ Highlights' in fragments['news']
print('news: 13 verified items, each with a source link')

# Publications
selected = yaml.safe_load((ROOT / 'data/selected_publications.yaml').read_text())
proot = roots['publications']
sel = by_class(proot, 'ag-site-paper', 'li')
assert len(sel) == len(selected)
# Selected Publications rules (Dylan, 2026-10-21): Electron Microscopy in Liquid first; Paul Alivisatos last author;
# 2025 on except Quantum Information Science; bold only for the first author and Paul Alivisatos.
areas_shown = [sec.get('id') for sec in proot.xpath('.//section[contains(@class,"ag-site-area")]')]
assert areas_shown and areas_shown[0] == 'selected-lctem', areas_shown
for p in selected:
    assert 'alivisatos' in p['authors'][-1].casefold(), p['doi']
    assert p['area'] == 'quantum' or int(p['year']) >= 2025, p['doi']
for li in sel:
    bold = [b.text_content() for b in by_class(li, 'ag-site-paper-authors', 'p')[0].xpath('.//strong')]
    names = [x.strip() for x in by_class(li, 'ag-site-paper-authors', 'p')[0].text_content().split(';')]
    n_first = sum(1 for x in names if x.endswith('*')) or 1
    assert bold and bold[:n_first] == names[:n_first] and all(b in names[:n_first] or 'Alivisatos' in b for b in bold), bold
for strong in by_class(proot, 'ag-site-pub-authors', 'p'):
    for b in strong.xpath('.//strong'):
        assert 'Alivisatos' in b.text_content(), 'full list: only Paul Alivisatos is bold'
import csv
n_rows = sum(1 for _ in csv.DictReader((ROOT / 'data/publications.csv').open()))
pubs = by_class(proot, 'ag-site-pub', 'li')
assert len(pubs) == n_rows
nums = [int(by_class(p, 'ag-site-pub-num', 'span')[0].text) for p in pubs]
assert nums == list(range(n_rows, 0, -1)), 'publications: numbering'
assert len(proot.xpath('.//section[contains(@class,"ag-site-year")]')) == 38
tags = yaml.safe_load((ROOT / 'data/publication_tags.yaml').read_text())
vocab = yaml.safe_load((ROOT / 'data/tags.yaml').read_text())
assert len({t['id'] for t in tags}) == len(tags) <= n_rows
for t in tags:
    for facet in ('areas', 'materials', 'approaches', 'applications'):
        for item in t.get(facet) or []:
            assert item['tag'] in vocab[facet], f'unknown tag {item}'
for f in re.findall(r'#(f-[\w-]+):target', styles['publications']):
    assert proot.xpath(f'.//*[@id="{f}"]'), f'publications: target {f} missing'
nfilters = len(set(re.findall(r'#(f-[\w-]+):target', styles['publications'])))
assert nfilters >= 20
assert not proot.xpath('.//img'), 'publications: <img> in this module makes WordPress render the page empty; use background images'
print(f'publications: {len(sel)} selected + {n_rows} numbered papers in 38 years; {nfilters} filters')

# Home
latest = sorted((p for p in selected if p.get('publication_date')), key=lambda p: p['publication_date'], reverse=True)[:3]
for paper in latest:
    assert 'https://doi.org/' + paper['doi'] in fragments['home']
home_news = yaml.safe_load((ROOT / 'data/home.yaml').read_text())
for item in home_news:
    assert item['source_url'] in fragments['home']
assert 'E247H' in fragments['home'] and 'mailto:alivisatos-lab@uchicago.edu' in fragments['home']
print('home: latest three papers, latest news with sources, research areas, contact block')

# Research: label corrections only
baseline = (ROOT / 'build/research-content.before-c.raw').read_text()
target = (ROOT / 'build/research-content.raw').read_text()
assert replace_research_citations(baseline) == target
print('research: journal label corrections reproducible')

# Module replacement is idempotent
for name in PAGES:
    marker = 'home-updates' if name == 'home' else name
    raw = '<!-- wp:divi/code ' + json.dumps({'content': {'innerContent': {'desktop': {'value': f'<!-- AUTO:{marker}:START --><!-- AUTO:{marker}:END -->'}}}}).replace('<', r'<').replace('>', r'>').replace('--', r'--') + ' /-->'
    once = replace_module(raw, fragments[name].strip(), marker, styles[name].strip())
    assert replace_module(once, fragments[name].strip(), marker, styles[name].strip()) == once
print('push: module and CSS replacement idempotent')
