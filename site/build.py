"""Render code-managed fragments from the publication and page data."""
from pathlib import Path
from datetime import date
import csv, json, html, os, re
from lxml import html as tree
from lxml import etree
import yaml
from push import BLOCK

ROOT=Path(__file__).resolve().parent
# Search boxes and filter buttons need a script. Page content on Voices drops <script>, so they are left out
# unless AG_INTERACTIVE=1 (set it only once the script can actually run on the live site).
INTERACTIVE=os.environ.get('AG_INTERACTIVE','0')=='1'
OUT=ROOT/'build'; OUT.mkdir(exist_ok=True)
records=list(csv.DictReader((ROOT/'data/publications.csv').open()))
if any(r['kind']!='publication' for r in records):
    raise ValueError('publications.csv must contain regular year-list records only')

AREA={
    'synthesis':('Synthesis and Properties','synthesis'),
    'lctem':('Electron Microscopy in Liquid','lctem'),
    'spectroscopy':('Spectroscopy and Structure','spectroscopy'),
    'quantum':('Quantum Information Science','quantum'),
}

def normalize_name(value):
    return re.sub(r'\s+',' ',re.sub(r'[^\w]+',' ',value.casefold())).strip()

selected_source=yaml.safe_load((ROOT/'data/selected_publications.yaml').read_text())
member_records=yaml.safe_load((ROOT/'data/members.yaml').read_text())
member_aliases={}
for member in member_records:
    for name in member.get('publication_names',[]):
        member_aliases[normalize_name(name)]=member.get('title_html',name)

def current_author_matches(paper):
    if int(paper.get('year',0))<2022:
        return []
    return [author for author in paper.get('authors',[]) if normalize_name(author) in member_aliases]

def card(r):
    attrs=json.loads(r['attributes'])
    attrs={k:(re.sub(r'\b(?:ap-|ag-pubs-|alivisatos-)','ag-site-',v) if k=='class' else v) for k,v in attrs.items()}
    attributes=' '.join(f'{k}="{html.escape(v,quote=True)}"' for k,v in attrs.items())
    journal_class=re.sub(r'\b(?:ap-|ag-pubs-|alivisatos-)','ag-site-',r['journal_class'])
    meta=f'<span class="{journal_class}">{r["journal_html"]}</span>'
    for cls,key in [('ag-site-year-tag','year'),('ag-site-citation-details','details_html')]:
        if r[key]: meta+=f'<span class="{cls}">{r[key]}</span>'
    if r['url']:
        if not r['url'].startswith('https://'): raise ValueError('HTTPS source link required')
        meta+=f'<a class="ag-site-doi" href="{html.escape(r["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(r["link_label"])}</a>'
    meta+=r['extra_meta_html']
    return f'<article {attributes}><h3 class="ag-site-card-title">{r["title_html"]}</h3><p class="ag-site-authors">{r["authors_html"]}</p><div class="ag-site-card-meta">{meta}</div></article>'

def initials_name(full_name):
    parts=full_name.split()
    if len(parts)<2: return full_name
    surname=parts[-1]
    initials=' '.join((part[0].upper()+'.') for part in parts[:-1])
    return f'{surname}, {initials}'

def citation_details(paper):
    volume=str(paper.get('volume') or '').strip()
    issue=str(paper.get('issue') or '').strip()
    number=str(paper.get('article_number') or paper.get('pages') or '').strip()
    if issue and volume: volume+=f' ({issue})'
    return f'{volume}, {number}' if volume and number else (volume or number)

def render_selected_paper(paper, matches):
    authors=[]
    for author in paper['authors']:
        label=html.escape(initials_name(author))
        if normalize_name(author) in member_aliases:
            label=f'<strong>{label}</strong>'
        authors.append(label)
    doi=paper['doi']
    slug=re.sub(r'[^a-z0-9]+','-',doi.casefold()).strip('-')
    doi_url='https://doi.org/'+doi
    if not doi.startswith('10.'):
        raise ValueError(f'Invalid DOI: {doi}')
    meta=[f'<span class="ag-site-citation">{html.escape(citation_details(paper))}</span>'] if citation_details(paper) else []
    meta.append(f'<a class="ag-site-paper-doi" href="{html.escape(doi_url,quote=True)}" target="_blank" rel="noopener noreferrer">DOI</a>')
    if paper.get('open_access'):
        meta.append('<span class="ag-site-open-access">Open access</span>')
    data_members='|'.join(matches)
    return (
        f'<li id="ag-pub-{slug}" class="ag-site-paper" data-area="{html.escape(paper["area"],quote=True)}" data-members="{html.escape(data_members,quote=True)}">'
        f'<span class="ag-site-paper-year">{int(paper["year"])}</span>'
        f'<div class="ag-site-paper-body"><span class="ag-site-paper-journal">{html.escape(paper["journal"])}</span>'
        f'<h3 class="ag-site-paper-title">{paper["title"]}</h3>'
        f'<p class="ag-site-paper-authors">{"; ".join(authors)}</p>'
        f'<div class="ag-site-paper-meta">{" ".join(meta)}</div></div></li>'
    )

eligible=[]
seen_dois=set()
for paper in selected_source:
    if paper['doi'] in seen_dois: raise ValueError(f'Duplicate selected DOI: {paper["doi"]}')
    seen_dois.add(paper['doi'])
    if paper.get('area') not in AREA: raise ValueError(f'Unknown research area: {paper.get("area")}')
    if paper.get('status')!='verified': raise ValueError(f'Unverified selected citation: {paper["doi"]}')
    matches=current_author_matches(paper)
    if matches: eligible.append((paper,matches))

area_html=[]
for area,(label,anchor) in AREA.items():
    papers=[(p,m) for p,m in eligible if p['area']==area]
    if not papers: continue
    papers.sort(key=lambda pair:pair[0].get('publication_date',''),reverse=True)
    cards='\n'.join(render_selected_paper(p,m) for p,m in papers)
    area_html.append(
        f'<section class="ag-site-area" id="ag-site-area-{area}" aria-labelledby="ag-site-area-heading-{area}">'
        f'<h3 class="ag-site-area-heading" id="ag-site-area-heading-{area}">{label}</h3>'
        f'<a class="ag-site-area-link" href="https://alivisatoslab.uchicago.edu/research/#{anchor}">About this research area</a>'
        f'<ul class="ag-site-list">{cards}</ul></section>'
    )
jumps=''.join(f'<a class="ag-site-chip" href="#ag-site-area-{area}">{AREA[area][0]}</a>' for area in AREA if any(p['area']==area for p,_ in eligible))
selected_html=(
    '<section class="ag-site-selected" aria-labelledby="ag-site-selected-heading">'
    '<header class="ag-site-selected-intro"><span class="ag-site-eyebrow">Alivisatos Group</span>'
    '<h2 class="ag-site-selected-heading" id="ag-site-selected-heading">Selected Publications</h2>'
    '<p class="ag-site-lede">Recent work by current group members, organized by research area. The complete publication list follows below.</p></header>'
    '<div><p class="ag-site-jump-label">Explore by research area</p><nav class="ag-site-jumps" aria-label="Jump to a research area">'+jumps+'</nav></div>'
    '<div class="ag-site-areas">'+'\n'.join(area_html)+'</div>'
    '<p class="ag-site-foot">Names in bold are current group members. DOI links open the publisher record.</p></section>'
)

def home_publication_card(paper):
    pub_date=date.fromisoformat(paper['publication_date'])
    date_text=f'{pub_date:%B} {pub_date.day}, {pub_date.year}'
    doi_url='https://doi.org/'+paper['doi']
    summary=paper.get('homepage_summary','')
    summary_html=f'<p class="ag-site-home-copy">{html.escape(summary)}</p>' if summary else ''
    return (
        '<article class="ag-site-home-paper">'
        f'<p class="ag-site-home-paper-date">{html.escape(paper["journal"])} · {html.escape(date_text)}</p>'
        f'<h3 class="ag-site-home-paper-title"><a href="{html.escape(doi_url,quote=True)}">{paper["title"]}</a></h3>'
        f'{summary_html}</article>'
    )

def area_label(slug):
    return {'synthesis':'Nanomaterial Synthesis','lctem':'Electron Microscopy in Liquid','spectroscopy':'Optical studies','quantum':'Quantum Information Science'}.get(slug,slug)

def render_member(record):
    rendered=record['template_html']
    for field in ('title_html','image_url','image_alt'):
        value=record.get(field,'')
        rendered=rendered.replace('@@'+field.upper()+'@@',value if field=='title_html' else html.escape(value,quote=True))
    root=tree.fragment_fromstring(rendered,create_parent='div')
    article=root.xpath('.//article')[0]
    article.set('class','ag-site-member-card')
    article.set('data-member-id',record['id'])
    content=article.xpath('./div')[0]
    content.set('class','ag-site-member-content')
    photo=article.xpath('./img')
    if photo:
        photo[0].set('class','ag-site-member-photo')
        photo[0].set('loading','lazy')
    name=content.xpath('./h3')[0]
    name.set('class','ag-site-member-name')
    # Personal emails stay on member cards (Dylan, 2026-10-20). Remove only the generic Research block.
    for block in content.xpath('.//div'):
        if 'Research Area:' in ' '.join(block.itertext()):
            parent=block.getparent()
            if parent is not None: parent.remove(block)
    role_text=''
    for block in content.xpath('./div'):
        text=' '.join(' '.join(block.itertext()).split())
        if text and 'Google Scholar' not in text and 'Education & links' not in text:
            role_text=text
            block.set('class','ag-site-member-role')
            break
    if not role_text:
        role_text='Principal Investigator' if record['id']=='members-001' else ''
    role_slug='postdoc' if 'postdoctoral' in role_text.casefold() else ('phd' if 'ph.d' in role_text.casefold() else ('undergraduate' if 'undergraduate' in role_text.casefold() else 'pi'))
    article.set('data-role',role_slug)
    match=re.search(r'(20\d{2})',role_text)
    if match: article.set('data-start-year',match.group(1))
    areas=record.get('areas',[])
    if areas:
        tags=tree.Element('div',attrib={'class':'ag-site-member-tags','aria-label':'Research areas'})
        for area in areas:
            label=area_label(area)
            if record['id']=='members-006': label='AI for Science, Electron Microscopy'
            if record['id']=='members-012': label={'synthesis':'Nanomaterial Synthesis','spectroscopy':'Optical studies'}[area]
            tag=etree.SubElement(tags,'a',attrib={'class':'ag-site-tag','href':f'https://alivisatoslab.uchicago.edu/research/#{area}'})
            tag.text=label
        pos=content.index(role_block:=next((e for e in content if e.tag=='div' and e.get('class')=='ag-site-member-role'),name))
        content.insert(pos+1,tags)
    scholar=article.xpath('.//a[contains(@href,"scholar.google.com")]')
    if scholar:
        actions=tree.Element('div',attrib={'class':'ag-site-member-actions','aria-label':'Profiles'})
        scholar_action=etree.SubElement(actions,'a',attrib={'class':'ag-site-member-action','href':scholar[0].get('href'),'target':'_blank','rel':'noopener noreferrer','aria-label':'Google Scholar profile'})
        scholar_action.text='Scholar ↗'
        content.insert(2 if len(content)>1 else len(content),actions)
    for details in content.xpath('.//details'):
        details.set('class','ag-site-member-details')
        for child in details.xpath('./div'):
            child.set('class','ag-site-details-body')
    for link in article.xpath('.//a'):
        if link.get('href','').startswith('https://alivisatoslab.uchicago.edu/research/'):
            link.set('class','ag-site-tag')
    return ''.join(tree.tostring(child,encoding='unicode',method='html') for child in root)

def render_alumni(records):
    labels={'phd':'Ph.D.','postdoc':'Postdoc','undergrad':'Undergraduate'}
    sectors=['university','industry','institute','unlisted']
    sector_labels={'university':'University','industry':'Industry','institute':'Institutes & national labs','unlisted':'Not listed'}
    counts={sector:sum(1 for r in records if r.get('sector')==sector) for sector in sectors}
    profs=sum(1 for r in records if 'professor' in r.get('title','').casefold())
    tmpl=(ROOT/'templates/alumni.html').read_text()
    tmpl=tmpl.replace('@@TOTAL@@',str(len(records))).replace('@@PROFESSORS@@',str(profs)).replace('@@INDUSTRY@@',str(counts['industry'])).replace('@@INSTITUTE@@',str(counts['institute']))
    bar=''.join(f'<span class="ag-site-sector-segment ag-site-sector-{sector}" data-sector-segment data-count="{counts[sector]}" data-total="{len(records)}" title="{html.escape(sector_labels[sector])}: {counts[sector]}"></span>' for sector in sectors)
    sector_buttons=['<button type="button" class="ag-site-filter-button" data-sector-filter data-value="all" aria-pressed="true">All sectors</button>']
    for sector in sectors:
        sector_buttons.append(f'<button type="button" class="ag-site-filter-button" data-sector-filter data-value="{sector}" aria-pressed="false">{html.escape(sector_labels[sector])} ({counts[sector]})</button>')
    role_buttons=['<button type="button" class="ag-site-filter-button" data-role-filter data-value="all" aria-pressed="true">All roles</button>']
    for role in ('phd','postdoc','undergrad'):
        count=sum(1 for r in records if role in r.get('roles',[]))
        role_buttons.append(f'<button type="button" class="ag-site-filter-button" data-role-filter data-value="{role}" aria-pressed="false">{labels[role]} ({count})</button>')
    cards=[]
    for record in sorted(records,key=lambda r:(r['name'].split()[-1].casefold(),r['name'].casefold())):
        roles=record.get('roles',[])
        name=html.escape(record['name'])
        title=html.escape(record.get('title',''))
        org=html.escape(record.get('org',''))
        haystack=' '.join([record['name'],record.get('title',''),record.get('org','')]).casefold()
        meta=' · '.join(x for x in (title,org,html.escape(record.get('years',''))) if x)
        name_html=f'<a href="{html.escape(record["link"],quote=True)}" target="_blank" rel="noopener noreferrer">{name}</a>' if record.get('link') else name
        tags=''.join(f'<span class="ag-site-role-tag">{labels[role]}</span>' for role in roles)
        cards.append(f'<article class="ag-site-alumni-card" data-alumni-card data-name="{html.escape(record["name"],quote=True)}" data-title="{html.escape(record.get("title",""),quote=True)}" data-org="{html.escape(record.get("org",""),quote=True)}" data-sector="{html.escape(record.get("sector","unlisted"),quote=True)}" data-roles="{html.escape("|".join(roles),quote=True)}" data-search="{html.escape(haystack,quote=True)}"><h2 class="ag-site-alumni-name">{name_html}</h2>{f"<p class=\"ag-site-alumni-meta\">{meta}</p>" if meta else ""}<div class="ag-site-role-tags">{tags}</div></article>')
    return tmpl.replace('@@SECTOR-BAR@@',bar).replace('@@SECTOR-FILTERS@@',''.join(sector_buttons)).replace('@@ROLE-FILTERS@@',''.join(role_buttons)).replace('@@ALUMNI-CARDS@@','\n'.join(cards))

def source_link(url,label='Source'):
    if not url.startswith('https://'): raise ValueError('HTTPS source link required')
    return f'<p class="ag-site-source"><a class="ag-site-link" href="{html.escape(url,quote=True)}" target="_blank" rel="noopener noreferrer">{html.escape(label)}</a></p>'

def render_news(record):
    if not record.get('publish',True): return ''
    if not record.get('source_url') or not record.get('verified'): raise ValueError(f'Published News item lacks verified source: {record["id"]}')
    rendered=record['template_html']
    for field in ('title_html','image_url','image_alt'):
        value=record.get(field,'')
        rendered=rendered.replace('@@'+field.upper()+'@@',value if field=='title_html' else html.escape(value,quote=True))
    return rendered.replace('</article>',source_link(record['source_url'])+'</article>')

def prefix_classes(root):
    for node in root.iter():
        if not isinstance(node.tag,str): continue
        node.attrib.pop('style',None)
        classes=node.get('class','').split()
        renamed=[]
        for cls in classes:
            if cls=='img': continue
            if cls.startswith(('ap-','ag-pubs-','alivisatos-')): cls='ag-site-'+cls.split('-',1)[1]
            renamed.append(cls)
        if renamed: node.set('class',' '.join(dict.fromkeys(renamed)))
        elif node.get('class') is not None: node.attrib.pop('class',None)
    for article in root.xpath('.//article'):
        if 'ag-site-card' not in article.get('class','').split() and 'ag-site-member-card' not in article.get('class','').split() and 'ag-site-alumni-card' not in article.get('class','').split() and 'ag-site-home-paper' not in article.get('class','').split():
            article.set('class',(article.get('class','')+' ag-site-card').strip())
        for img in article.xpath('./img'):
            # Member photos keep their own size rule; only other cards get the full-width card image.
            if 'ag-site-member-photo' not in img.get('class','').split():
                img.set('class','ag-site-card-image')
        for time_node in article.xpath('.//time'):
            p=time_node.getparent()
            if p is not None and p.tag=='p': p.set('class','ag-site-kicker')
        for h in article.xpath('.//h2'):
            if not h.get('class'): h.set('class','ag-site-card-title')
        for h in article.xpath('.//h3'):
            if not h.get('class'): h.set('class','ag-site-home-news-title')
        for p in article.xpath('./div//p'):
            if not p.get('class') and not p.xpath('.//time'): p.set('class','ag-site-card-copy')
        content=article.xpath('./div[not(@aria-hidden="true")]')
        if content and not content[0].get('class'): content[0].set('class','ag-site-card-content')
        placeholder=article.xpath('./div[@aria-hidden="true"]')
        if placeholder: placeholder[0].set('class','ag-site-news-placeholder')
    # Divi's Code module can strip stylesheet blocks; inline matching rules from the shared CSS source.
    css=re.sub(r'/\*[\s\S]*?\*/','',(ROOT/'assets/site.css').read_text())
    rules=[(selector.strip(),re.sub(r'\s+',' ',body.strip())) for group,body in re.findall(r'([^{}]+)\{([^{}]+)\}',css) if not group.strip().startswith('@') for selector in group.split(',')]
    def matches_simple(node,selector,extra_classes=()):
        required=re.findall(r'\.([\w-]+)',selector)
        present=set(node.get('class','').split())|set(extra_classes)
        if any(c not in present for c in required): return False
        tag=selector.split('.',1)[0].strip()
        return not tag or tag==node.tag
    def matches_selector(node,selector,extra_classes=()):
        parts=selector.split()
        if not parts or not matches_simple(node,parts[-1],extra_classes): return False
        ancestor=node.getparent()
        for part in reversed(parts[:-1]):
            while ancestor is not None and (not isinstance(ancestor.tag,str) or not matches_simple(ancestor,part)):
                ancestor=ancestor.getparent()
            if ancestor is None: return False
            ancestor=ancestor.getparent()
        return True
    def style_for(node,extra_classes=()):
        return ' '.join(body for selector,body in rules if matches_selector(node,selector,extra_classes))
    for node in root.iter():
        if not isinstance(node.tag,str): continue
        declarations=style_for(node)
        if declarations: node.set('style',declarations)
        if 'data-sector-segment' in node.attrib:
            # Width set at build time so the bar renders without a script.
            share=100*int(node.get('data-count','0'))/max(int(node.get('data-total','1')),1)
            node.set('style',((declarations+' ') if declarations else '')+f'width: {share:.2f}%;')
        if 'ag-site-filter-button' in node.get('class','').split():
            node.set('data-base-style',declarations)
            node.set('data-active-style',style_for(node,('ag-site-active',)))
    return root

def strip_controls(root):
    """Remove script-dependent controls (search boxes, filter buttons) so no dead UI is published."""
    for cls in ('ag-site-publication-tools','ag-site-alumni-tools','ag-site-filter-row'):
        for el in root.xpath(f'.//*[contains(concat(" ",normalize-space(@class)," ")," {cls} ")]'):
            el.getparent().remove(el)

def build_research_corrections():
    source=ROOT/'build/research-content.before-c.raw'
    raw=source.read_text()
    counts={'Synth':0,'Adv':0,'JACS':0}
    def walk(value):
        if isinstance(value,str):
            replacements=[(' Synth</em>',' Nat. Synth</em>'),('Adv.</em>','Sci. Adv.</em>'),('J. Am. Chem. Soc</em>. 2023','J. Am. Chem. Soc.</em> 2023')]
            for before,after in replacements:
                n=value.count(before)
                if before.startswith(' Synth'): counts['Synth']+=n
                elif before.startswith('Adv.'): counts['Adv']+=n
                else: counts['JACS']+=n
                value=value.replace(before,after)
            return value
        if isinstance(value,dict): return {k:walk(v) for k,v in value.items()}
        if isinstance(value,list): return [walk(v) for v in value]
        return value
    def replace(m):
        before=json.loads(m.group(2));after=walk(before)
        if before==after: return m.group(0)
        encoded=json.dumps(after,ensure_ascii=False,separators=(',',':'))
        for char,escaped in [('--',r'\u002d\u002d'),('<',r'\u003c'),('>',r'\u003e'),('&',r'\u0026')]: encoded=encoded.replace(char,escaped)
        return '<!-- wp:'+m.group(1)+' '+encoded+' '+m.group(3)+'-->'
    updated=BLOCK.sub(replace,raw)
    found={'Synth':0,'Adv':0,'JACS':0}
    for match in BLOCK.finditer(updated):
        block=json.loads(match.group(2))
        def inspect(value):
            if isinstance(value,str):
                found['Synth']+=value.count('Nat. Synth</em>')
                found['Adv']+=value.count('Sci. Adv.</em>')
                found['JACS']+=value.count('J. Am. Chem. Soc.</em> 2023')
            elif isinstance(value,dict):
                for item in value.values(): inspect(item)
            elif isinstance(value,list):
                for item in value: inspect(item)
        inspect(block)
    if found!={'Synth':1,'Adv':1,'JACS':1}: raise ValueError(f'Unexpected corrected Research citation counts: {found}')
    (ROOT/'build/research-content.raw').write_text(updated)
    import difflib
    diff=''.join(difflib.unified_diff(raw.splitlines(True),updated.splitlines(True),fromfile='research-before.raw',tofile='research-corrected.raw'))
    (ROOT/'reports/research-c.diff').write_text(diff)
    return counts

# C: make the three Research citation fixes while retaining every Divi block and attribute.
research_counts=build_research_corrections()

years=sorted({r['group'] for r in records},key=lambda y:1980 if y=='1980s' else int(y),reverse=True)
year_template=(ROOT/'templates/publication-year.html').read_text()
current_year=date.today().year
years_html='\n'.join(year_template.replace('@@YEAR@@',year).replace('@@CARDS@@','\n'.join(card(r) for r in records if r['group']==year)).replace('@@DEFAULT_OPEN@@','true' if year!='1980s' and int(year)>=current_year-3 else 'false').replace('@@OPEN@@',' open' if year!='1980s' and int(year)>=current_year-3 else '') for year in years)
nav='<nav class="ag-site-year-nav" aria-label="Publication years">'+'\n'.join(f'<a href="#pub-{year}">{year}</a>' for year in years)+'</nav>'
module=(ROOT/'templates/publications.html').read_text().replace('@@YEARS@@',years_html).replace('@@NAV@@',nav).replace('@@SELECTED@@',selected_html)
fragments={'publications':module}
home_records=yaml.safe_load((ROOT/'data/home.yaml').read_text())
members=yaml.safe_load((ROOT/'data/members.yaml').read_text())
for name in ('members','alumni','news'):
    module=(ROOT/'templates'/f'{name}.html').read_text()
    if name=='members':
        for i,record in enumerate(members,1): module=module.replace(f'@@MEMBERS-{i}@@',render_member(record))
    elif name=='alumni':
        module=render_alumni(yaml.safe_load((ROOT/'data/alumni.yaml').read_text()))
    else:
        items=yaml.safe_load((ROOT/'data/news.yaml').read_text())
        for i,record in enumerate(items,1): module=module.replace(f'@@NEWS-{i}@@',render_news(record))
    fragments[name]=module

home_module=(ROOT/'templates/home.html').read_text()
latest=sorted((p for p,_ in eligible if p.get('publication_date')),key=lambda p:p['publication_date'],reverse=True)[:3]
if len(latest)!=3: raise ValueError('Home Latest Publications requires three dated selected records')
home_module=home_module.replace('@@HOME-PUBLICATIONS@@','\n'.join(home_publication_card(p) for p in latest))
for i,record in enumerate(home_records,1):
    rendered=record['template_html'].replace('@@TITLE_HTML@@',record['title_html'])
    if not record.get('source_url'): raise ValueError(f'Home Latest News item lacks a source: {record["id"]}')
    home_module=home_module.replace(f'@@HOME-NEWS-{i}@@',rendered.replace('</article>',source_link(record['source_url'])+'</article>'))
fragments['home']=home_module

def validate_markers(fragment,name):
    stack=[]
    for marker,kind in re.findall(r'<!--\s*AUTO:([^:]+):(START|END)\s*-->',fragment):
        if kind=='START': stack.append(marker)
        elif not stack or stack.pop()!=marker: raise ValueError(f'Unbalanced AUTO markers in {name}: {marker}')
    if stack: raise ValueError(f'Unclosed AUTO markers in {name}: {stack}')

css=(ROOT/'assets/site.css').read_text()
integration=(ROOT/'assets/site-integration.html').read_text()
for name,fragment in fragments.items():
    assert not re.search(r'sci[-.]?hub',fragment,re.I),'Unexpected non-publisher link'
    assert '@@' not in fragment,'Unresolved template variable'
    validate_markers(fragment,name)
    main_marker='home-updates' if name=='home' else name
    if fragment.count(f'<!-- AUTO:{main_marker}:START -->')!=1 or fragment.count(f'<!-- AUTO:{main_marker}:END -->')!=1:
        raise ValueError(f'Missing main AUTO marker in {name}')
    root=prefix_classes(tree.fragment_fromstring(fragment,create_parent='div'))
    if not INTERACTIVE: strip_controls(root)
    rendered=''.join(tree.tostring(child,encoding='unicode',method='html') for child in root)
    if re.search(r'class="[^"]*(?:ap-|ag-pubs-|alivisatos-)',''.join(root.itertext())):
        raise ValueError(f'Legacy class prefix remains in {name}')
    if root.xpath('.//style'): raise ValueError(f'Style blocks cannot be used in Divi Code modules ({name})')
    if root.xpath('.//script'): raise ValueError(f'Interactive scripts belong in Divi Integration, not the sanitized page module ({name})')
    (OUT/f'{name}.html').write_text(rendered)
    (OUT/f'{name}-preview.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+name+'</title>'+integration+'</head><body><main>'+rendered+'</main></body></html>')

print(f'Built {len(fragments)} fragments; {len(records)} regular publication cards, {len(eligible)} selected papers; Research fixes {research_counts}.')
