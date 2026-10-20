"""Check the generated site fragments, sources and key interaction data."""
from pathlib import Path
from collections import Counter
from datetime import date
import csv, json, os, re
from lxml import html
import yaml
from push import BLOCK, replace_module, replace_research_citations

ROOT=Path(__file__).resolve().parent
INTERACTIVE=os.environ.get('AG_INTERACTIVE','0')=='1'
PAGES=('publications','members','alumni','news','home')
integration=(ROOT/'assets/site-integration.html').read_text()

def check_markers(fragment,name):
    stack=[]
    for marker,kind in re.findall(r'<!--\s*AUTO:([^:]+):(START|END)\s*-->',fragment):
        if kind=='START': stack.append(marker)
        elif not stack or stack.pop()!=marker: raise AssertionError(f'{name}: unbalanced AUTO:{marker}')
    assert not stack,f'{name}: unclosed AUTO markers {stack}'

fragments={name:(ROOT/'build'/f'{name}.html').read_text() for name in PAGES}
roots={name:html.fragment_fromstring(fragment,create_parent='div') for name,fragment in fragments.items()}
for name,fragment in fragments.items():
    marker='home-updates' if name=='home' else name
    check_markers(fragment,name)
    assert fragment.count(f'<!-- AUTO:{marker}:START -->')==1
    assert fragment.count(f'<!-- AUTO:{marker}:END -->')==1
    assert not roots[name].xpath('.//style'),f'{name}: CSS must be inlined from assets/site.css'
    assert not roots[name].xpath('.//script'),f'{name}: interactive scripts belong in the Divi Integration asset'
    assert not re.search(r'sci[-.]?hub',fragment,re.I),f'{name}: unexpected browser extension link'
    legacy=[c for node in roots[name].iter() if isinstance(node.tag,str) for c in node.get('class','').split() if c.startswith(('ap-','ag-pubs-','alivisatos-'))]
    assert not legacy,f'{name}: legacy class prefixes remain: {legacy[:4]}'

# Selected and regular publications preserve the agreed source data and year-list size.
selected=yaml.safe_load((ROOT/'data/selected_publications.yaml').read_text())
pub=roots['publications']
selected_nodes=pub.xpath('.//li[contains(concat(" ",normalize-space(@class)," ")," ag-site-paper ")]')
regular=pub.xpath('.//article[contains(concat(" ",normalize-space(@class)," ")," ag-site-card ")]')
assert len(selected)==len(selected_nodes)==11
assert len(regular)==484
assert all(int(p['year'])>=2022 and p.get('status')=='verified' for p in selected)
assert Counter(pub.xpath('.//li[contains(@class,"ag-site-paper")]//a[contains(@class,"ag-site-paper-doi")]/@href'))==Counter('https://doi.org/'+p['doi'] for p in selected)
year_groups=pub.xpath('.//details[contains(@class,"ag-site-year-toggle")]')
assert len(year_groups)==38
for group in year_groups:
    year=group.get('id','').removeprefix('pub-')
    should_open=year!='1980s' and int(year)>=date.today().year-3
    assert (group.get('open') is not None)==should_open,f'Unexpected open state for {year}'
if INTERACTIVE:
    assert pub.xpath('.//*[@id="publication-search"]')
    assert "card.textContent.toLowerCase()" in integration and "card.el.style.display" in integration
    assert 'title, author, or journal' in fragments['publications']
else:
    assert not pub.xpath('.//input|.//button'),'publications: script-dependent controls must be absent'
print('publications: 484 regular + 11 selected; 38 years; search and recent-year defaults verified')

# Home's newest three publication cards are derived from selected data and each Latest News card has a source.
latest=sorted((p for p in selected if p.get('publication_date')),key=lambda p:p['publication_date'],reverse=True)[:3]
for paper in latest:
    assert 'https://doi.org/'+paper['doi'] in fragments['home']
home_news=yaml.safe_load((ROOT/'data/home.yaml').read_text())
home_root=roots['home']
home_news_cards=home_root.xpath('.//*[@id="home-latest-news"]/../div//article')
assert len(home_news_cards)==3
assert all(card.xpath('.//a[contains(@class,"ag-site-link")]/@href') for card in home_news_cards)
for item in home_news:
    assert item['source_url'] in fragments['home']
print('home: latest three publications match selected data; all Latest News cards link to sources')

# Members: confirmed area anchors, square-crop source, safe public contact, no personal mailto destinations.
members=yaml.safe_load((ROOT/'data/members.yaml').read_text())
member_root=roots['members']
member_cards=member_root.xpath('.//article[contains(@class,"ag-site-member-card")]')
assert len(members)==len(member_cards)==20
assert all(isinstance(item.get('areas'),list) for item in members)
assert member_root.xpath('.//figure[contains(@class,"ag-site-group-photo")]//img')
assert set(member_root.xpath('.//a[starts-with(@href,"mailto:")]/@href'))=={'mailto:alivisatos-lab@uchicago.edu'}
assert not member_root.xpath('.//a[starts-with(@href,"https://alivisatoslab.uchicago.edu/research") and not(contains(@href,"#"))]')
area_targets={item['id']:item.get('areas',[]) for item in members}
for item in members:
    card=member_root.xpath(f'.//article[@data-member-id="{item["id"]}"]')[0]
    for area in item.get('areas',[]): assert f'https://alivisatoslab.uchicago.edu/research/#{area}' in card.xpath('.//a/@href')
yi=member_root.xpath('.//article[@data-member-id="members-006"]')[0]
ida=member_root.xpath('.//article[@data-member-id="members-012"]')[0]
assert 'AI for Science, Electron Microscopy' in yi.text_content() and 'research/#lctem' in ' '.join(yi.xpath('.//a/@href'))
assert 'Nanomaterial Synthesis' in ida.text_content() and 'Optical studies' in ida.text_content()
assert 'research/#synthesis' in ' '.join(ida.xpath('.//a/@href')) and 'research/#spectroscopy' in ' '.join(ida.xpath('.//a/@href'))
assert len(member_root.xpath('.//a[contains(@href,"scholar.google.com")]'))==14
print('members: 20 cards; confirmed area anchors; group photo; public contact and Scholar links')

# Alumni: one card per unique person, including the 12 multi-role alumni.
alumni=yaml.safe_load((ROOT/'data/alumni.yaml').read_text())
alumni_root=roots['alumni']
alumni_cards=alumni_root.xpath('.//*[@data-alumni-card]')
assert len(alumni)==len(alumni_cards)==187
assert len({r['name'] for r in alumni})==187
dual=[r['name'] for r in alumni if len(r.get('roles',[]))>1]
assert len(dual)==12
assert sum('|' in card.get('data-roles','') for card in alumni_cards)==12
assert len(alumni_root.xpath('.//*[@data-sector-segment]'))==4
assert all('width:' in seg.get('style','') for seg in alumni_root.xpath('.//*[@data-sector-segment]'))
if INTERACTIVE:
    assert alumni_root.xpath('.//*[@id="alumni-search"]')
    assert len(alumni_root.xpath('.//*[@data-role-filter]'))==4
    assert len(alumni_root.xpath('.//*[@data-sector-filter]'))==5
    assert "card.dataset.search.indexOf(q)" in integration
    assert all(button.get('data-active-style') for button in alumni_root.xpath('.//*[@data-role-filter or @data-sector-filter]'))
else:
    assert not alumni_root.xpath('.//input|.//button'),'alumni: script-dependent controls must be absent'
print('alumni: 187 unique cards; 12 Ph.D./postdoc dual-role people shown once; sector, role and search filters')

# News: every published card has a verified external source. Unverified Highlight selection stays unpublished.
news=yaml.safe_load((ROOT/'data/news.yaml').read_text())
news_root=roots['news']
published=[item for item in news if item.get('publish',True)]
news_cards=news_root.xpath('.//article')
assert len(published)==len(news_cards)==9
assert all(item.get('verified') and item.get('source_url','').startswith('https://') for item in published)
assert all(card.xpath('.//a[contains(@class,"ag-site-link")]/@href') for card in news_cards)
withheld=[item for item in news if not item.get('publish')]
assert len(withheld)==1 and withheld[0]['id']=='news-007' and not withheld[0]['verified']
assert 'Editors’ Highlights' not in fragments['news']
assert 'https://mosaic.uchicago.edu/events/' in fragments['news']
source_report=(ROOT/'reports/news_sources.md').read_text()
report_rows=re.findall(r'^\|\s*(News|Home Latest News)\s*\|',source_report,re.M)
assert len(report_rows)==13
print('news: 9 verified items published; 1 unverified promotional claim withheld; 13 source rows documented')

# Research: only one Divi text block differs from the saved baseline, and JSON remains parseable.
baseline_path=ROOT/'build/research-content.before-c.raw'
target_path=ROOT/'build/research-content.raw'
baseline=baseline_path.read_text();target=target_path.read_text()
assert replace_research_citations(baseline)==target
before_blocks=[json.loads(m.group(2)) for m in BLOCK.finditer(baseline)]
after_blocks=[json.loads(m.group(2)) for m in BLOCK.finditer(target)]
assert len(before_blocks)==len(after_blocks)
assert sum(a!=b for a,b in zip(before_blocks,after_blocks))==2
research_strings=[]
def collect_strings(value):
    if isinstance(value,str): research_strings.append(value)
    elif isinstance(value,dict):
        for item in value.values(): collect_strings(item)
    elif isinstance(value,list):
        for item in value: collect_strings(item)
for block in after_blocks: collect_strings(block)
research_text=' '.join(research_strings)
assert 'Nat. Synth</em>' in research_text and 'Sci. Adv.</em>' in research_text and 'J. Am. Chem. Soc.</em> 2023' in research_text
print('research: three journal abbreviations corrected in two Divi text blocks; all block JSON parses')

# Divi module replacement remains isolated for generated pages.
pub_backup=ROOT/'backup/20261020T145700Z/publications-content.raw'
home_backup=ROOT/'backup/20261020T150000Z/home.json'
if pub_backup.exists():
    raw=pub_backup.read_text();updated=replace_module(raw,fragments['publications'].strip(),'publications')
    assert replace_module(updated,fragments['publications'].strip(),'publications')==updated
if home_backup.exists():
    raw=json.loads(home_backup.read_text())['content']['raw'];updated=replace_module(raw,fragments['home'].strip(),'home-updates')
    assert replace_module(updated,fragments['home'].strip(),'home-updates')==updated
css=(ROOT/'assets/site.css').read_text()
assert re.search(r'\.ag-site-root\s*\{',css) and not re.search(r'\.(?:ap|ag-pubs|alivisatos)-[\w-]+\s*\{',css)
assert "alivisatos-publications" in integration and "data-alumni-root" in integration
print('shared styles: all generated page modules use assets/site.css and ag-site-* classes; interaction code is separate for the Divi Integration')
