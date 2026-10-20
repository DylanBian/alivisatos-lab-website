"""Render the code-managed page sections (AUTO modules) and their stylesheet from the data files.

For each page, writes build/<page>.html (the AUTO module content) and build/<page>.css (the Free-Form CSS that
push.py stores on the same Divi Code module). Saving page content on Voices removes <style> and <script> and filters
inline style properties; Divi module CSS is kept and printed on that page only (tested 2026-10-20).
Filters work without scripts: chips link to #targets and CSS rules use :target.
"""
from pathlib import Path
from datetime import date
from collections import Counter
import html, json, re
from lxml import html as tree
import yaml
from push import BLOCK, replace_research_citations
import pubdata

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'build'
OUT.mkdir(exist_ok=True)
SITE = 'https://alivisatoslab.uchicago.edu'
LAB_EMAIL = 'alivisatos-lab@uchicago.edu'
ADDRESS_LINES = ['Gordon Center for Integrative Science, Room E247H', '929 E 57th Street', 'Chicago, IL 60637']
MAP_URL = 'https://www.google.com/maps/search/?api=1&query=929+E+57th+Street+Chicago+IL+60637'
NOSCROLL = 'et_smooth_scroll_disabled'  # Divi intercepts in-page links for smooth scrolling unless this class is set

TAGS = yaml.safe_load((ROOT / 'data/tags.yaml').read_text())
AREA_ORDER = ['synthesis', 'lctem', 'spectroscopy', 'quantum']
AREA_PAGE_LABEL = {
    'synthesis': 'Synthesis and Properties of Nanoparticles',
    'lctem': 'Advancing Electron Microscopy in Liquid',
    'spectroscopy': 'Spectroscopy and Structural Studies',
    'quantum': 'Quantum Information Science',
}
esc = lambda s: html.escape(str(s), quote=True)


def norm(value):
    return re.sub(r'\s+', ' ', re.sub(r'[^\w]+', ' ', value.casefold())).strip()


members = yaml.safe_load((ROOT / 'data/members.yaml').read_text())
member_aliases = {}
for m in members:
    if m['group'] == 'pi':
        continue
    for name in m.get('publication_names', []) + [m['name']]:
        member_aliases[norm(name)] = m['name']

# ---------------------------------------------------------------- shared pieces
def contact_block(heading_id):
    address = '<br>'.join(esc(x) for x in ADDRESS_LINES)
    return (
        f'<section class="ag-site-section" aria-labelledby="{heading_id}">'
        f'<h2 class="ag-site-section-title" id="{heading_id}">Contact</h2>'
        '<div class="ag-site-contact">'
        f'<div><h3>Address</h3><p>Alivisatos Group<br>{address}</p></div>'
        f'<div><h3>Inquiries</h3><p><a href="mailto:{LAB_EMAIL}">{LAB_EMAIL}</a></p></div>'
        f'<div><h3>Directions</h3><p><a href="{esc(MAP_URL)}" target="_blank" rel="noopener noreferrer">Open in Google Maps</a></p></div>'
        '</div></section>'
    )


def chip(href, label, count=None, extra=''):
    count_html = f' <span class="ag-site-chip-count">{count}</span>' if count is not None else ''
    return f'<a class="ag-site-chip {NOSCROLL}{extra}" href="{href}">{esc(label)}{count_html}</a>'


def filter_css(root_class, target_id, hide_selector, chip_href):
    """CSS for one :target filter: hide non-matching items, mark the chip, show the status line."""
    return (f'.ag-site-root.{root_class}:has(#{target_id}:target) {hide_selector}{{display:none}}'
            f'.ag-site-root.{root_class}:has(#{target_id}:target) .ag-site-chip[href="{chip_href}"]{{border-color:#800000;background:#800000;color:#fff}}'
            f'.ag-site-root.{root_class}:has(#{target_id}:target) .ag-site-chip[href="{chip_href}"] .ag-site-chip-count{{color:#f3dede}}'
            f'.ag-site-root.{root_class}:has(#{target_id}:target) .ag-site-status-{target_id}{{display:block}}'
            f'.ag-site-root.{root_class}:has(#{target_id}:target) .ag-site-chip-all{{border-color:#e6dfdf;background:#fff;color:#2b2324}}')


# ---------------------------------------------------------------- members
GROUPS = [('pi', 'Principal Investigator'), ('postdoc', 'Postdoctoral Researchers'),
          ('phd', 'Graduate Students'), ('undergrad', 'Undergraduate Students')]


def member_links(m):
    links = []
    if m.get('email'):
        links.append(f'<a href="mailto:{esc(m["email"])}">{esc(m["email"])}</a>')
    if m.get('scholar'):
        links.append(f'<a href="{esc(m["scholar"])}" target="_blank" rel="noopener noreferrer">Google Scholar ↗</a>')
    return f'<div class="ag-site-member-links">{"".join(links)}</div>' if links else ''


def render_member(m):
    research = ''
    if m.get('research'):
        tags = ''.join(f'<a class="ag-site-tag" href="{SITE}/research/#{esc(r["area"])}">{esc(r["text"])}</a>' for r in m['research'])
        research = f'<div class="ag-site-member-research" aria-label="Research">{tags}</div>'
    details = ''
    if m.get('education'):
        items = ''.join(f'<li>{esc(x)}</li>' for x in m['education'])
        details = f'<details class="ag-site-member-details"><summary>Education</summary><ul>{items}</ul></details>'
    start = f' data-start="{m["start"]}"' if m.get('start') else ''
    return (
        f'<article class="ag-site-member-card" id="{esc(m["id"])}" data-group="{m["group"]}"{start}>'
        f'<img class="ag-site-member-photo" src="{esc(m["photo"])}" alt="{esc(m["photo_alt"])}" loading="lazy">'
        f'<div class="ag-site-member-body"><h3 class="ag-site-member-name">{esc(m["display_name"])}</h3>'
        f'<p class="ag-site-member-role">{esc(m["role"])}</p>{research}{member_links(m)}{details}</div></article>'
    )


def render_pi(m):
    roles = ''.join(f'<p class="ag-site-pi-role">{esc(x)}</p>' for x in m.get('role_lines', []))
    career = ''
    if m.get('career'):
        items = ''.join(f'<li>{esc(x)}</li>' for x in m['career'])
        career = f'<details class="ag-site-member-details"><summary>Education and career</summary><ul>{items}</ul></details>'
    return (
        f'<article class="ag-site-pi" id="{esc(m["id"])}" data-group="pi">'
        f'<img class="ag-site-pi-photo" src="{esc(m["photo"])}" alt="{esc(m["photo_alt"])}" loading="lazy">'
        f'<div><h3 class="ag-site-pi-name">{esc(m["display_name"])}</h3>{roles}{member_links(m)}{career}</div></article>'
    )


def build_members():
    sections = []
    for key, label in GROUPS:
        people = [m for m in members if m['group'] == key]
        if not people:
            continue
        hid = 'members-' + re.sub(r'[^a-z]+', '-', label.casefold()).strip('-')
        body = render_pi(people[0]) if key == 'pi' else '<div class="ag-site-member-grid">' + ''.join(render_member(m) for m in people) + '</div>'
        sections.append(f'<section class="ag-site-section" aria-labelledby="{hid}"><h2 class="ag-site-section-title" id="{hid}">{label}</h2>{body}</section>')
    alumni_note = (f'<p class="ag-site-view-all"><a href="{SITE}/alumni/">Former members: see Alumni →</a></p>')
    return ('<!-- AUTO:members:START -->\n<div id="alivisatos-members" class="ag-site-root ag-site-members">'
            '<h1 class="ag-site-title">Current Members</h1>' + ''.join(sections) + alumni_note
            + contact_block('members-contact') + '</div>\n<!-- AUTO:members:END -->'), ''


# ---------------------------------------------------------------- alumni
def build_alumni():
    records = yaml.safe_load((ROOT / 'data/alumni.yaml').read_text())
    labels = {'phd': 'Ph.D.', 'postdoc': 'Postdoc', 'undergrad': 'Undergraduate'}
    sectors = ['university', 'industry', 'institute', 'unlisted']
    sector_labels = {'university': 'University', 'industry': 'Industry', 'institute': 'Institutes and national labs', 'unlisted': 'Not listed'}
    counts = Counter(r.get('sector', 'unlisted') for r in records)
    profs = sum(1 for r in records if 'professor' in r.get('title', '').casefold())
    total = len(records)
    stats = (f'<section class="ag-site-alumni-summary" aria-label="Alumni summary">'
             f'<div class="ag-site-stat"><strong class="ag-site-stat-value">{total}</strong><span class="ag-site-stat-label">Alumni listed</span></div>'
             f'<div class="ag-site-stat"><strong class="ag-site-stat-value">{profs}</strong><span class="ag-site-stat-label">Professors</span></div>'
             f'<div class="ag-site-stat"><strong class="ag-site-stat-value">{counts["industry"]}</strong><span class="ag-site-stat-label">In industry</span></div>'
             f'<div class="ag-site-stat"><strong class="ag-site-stat-value">{counts["institute"]}</strong><span class="ag-site-stat-label">At institutes and national labs</span></div></section>')
    bar = ''.join(f'<span class="ag-site-sector-segment ag-site-sector-{s}" style="width:{100 * counts[s] / total:.2f}%" title="{esc(sector_labels[s])}: {counts[s]}"></span>' for s in sectors)
    filters, css, statuses = [], [], []
    targets = []
    sector_chips = [chip('#alumni-all', 'All', total, ' ag-site-chip-all')]
    for s in sectors:
        tid = f'alumni-sector-{s}'
        targets.append(tid)
        sector_chips.append(chip(f'#{tid}', sector_labels[s], counts[s]).replace('">', f'"><span class="ag-site-dot ag-site-sector-{s}" aria-hidden="true"></span>', 1))
        css.append(filter_css('ag-site-alumni', tid, f'.ag-site-alumni-card:not([data-sector="{s}"])', f'#{tid}'))
        statuses.append(f'<p class="ag-site-filter-status ag-site-status-{tid}">Showing {counts[s]} alumni: {esc(sector_labels[s])}.<a class="{NOSCROLL}" href="#alumni-all">Show all</a></p>')
    role_chips = []
    for role in ('phd', 'postdoc', 'undergrad'):
        n = sum(1 for r in records if role in r.get('roles', []))
        tid = f'alumni-role-{role}'
        targets.append(tid)
        role_chips.append(chip(f'#{tid}', labels[role], n))
        css.append(filter_css('ag-site-alumni', tid, f'.ag-site-alumni-card:not(.ag-site-r-{role})', f'#{tid}'))
        statuses.append(f'<p class="ag-site-filter-status ag-site-status-{tid}">Showing {n} alumni: {labels[role]}.<a class="{NOSCROLL}" href="#alumni-all">Show all</a></p>')
    filters.append(f'<div class="ag-site-filter-group"><span class="ag-site-filter-label">Sector</span>{"".join(sector_chips)}</div>')
    filters.append(f'<div class="ag-site-filter-group"><span class="ag-site-filter-label">Role in group</span>{"".join(role_chips)}</div>')
    cards = []
    for r in sorted(records, key=lambda r: (r['name'].split()[-1].casefold(), r['name'].casefold())):
        roles = r.get('roles', [])
        name = esc(r['name'])
        meta = ' · '.join(x for x in (esc(r.get('title', '')), esc(r.get('org', '')), esc(r.get('years', ''))) if x)
        name_html = f'<a href="{esc(r["link"])}" target="_blank" rel="noopener noreferrer">{name}</a>' if r.get('link') else name
        tags = ''.join(f'<span class="ag-site-role-tag">{labels[x]}</span>' for x in roles)
        role_classes = ''.join(f' ag-site-r-{x}' for x in roles)
        meta_html = f'<p class="ag-site-alumni-meta">{meta}</p>' if meta else ''
        cards.append(f'<article class="ag-site-alumni-card{role_classes}" data-sector="{esc(r.get("sector", "unlisted"))}">'
                     f'<h3 class="ag-site-alumni-name">{name_html}</h3>{meta_html}<div class="ag-site-role-tags">{tags}</div></article>')
    target_html = '<span class="ag-site-target" id="alumni-all"></span>' + ''.join(f'<span class="ag-site-target" id="{t}"></span>' for t in targets)
    module = ('<!-- AUTO:alumni:START -->\n<div id="alivisatos-alumni" class="ag-site-root ag-site-alumni">'
              '<h1 class="ag-site-title">Alumni</h1>'
              '<p class="ag-site-lede">Former Ph.D. students, postdoctoral researchers and undergraduates of the Alivisatos Group, with their current positions where known.</p>'
              + stats +
              '<section class="ag-site-section" aria-labelledby="alumni-sector-heading">'
              '<h2 class="ag-site-section-title" id="alumni-sector-heading">Where they are now</h2>'
              f'<div class="ag-site-sector-bar" role="img" aria-label="Alumni by sector">{bar}</div>'
              + target_html + '<div class="ag-site-filters">' + ''.join(filters) + '</div>' + ''.join(statuses) +
              '<div class="ag-site-alumni-grid">' + '\n'.join(cards) + '</div></section>'
              f'<p class="ag-site-corrections">For corrections or updates to this page, please email <a href="mailto:{LAB_EMAIL}">{LAB_EMAIL}</a>.</p>'
              '</div>\n<!-- AUTO:alumni:END -->')
    return module, ''.join(css)


# ---------------------------------------------------------------- news
def strip_styles(fragment):
    root = tree.fragment_fromstring(fragment, create_parent='div')
    for node in root.iter():
        if isinstance(node.tag, str):
            node.attrib.pop('style', None)
    return root


def news_card(record):
    rendered = record['template_html']
    for field in ('title_html', 'image_url', 'image_alt'):
        value = record.get(field, '')
        rendered = rendered.replace('@@' + field.upper() + '@@', value if field == 'title_html' else esc(value))
    root = strip_styles(rendered)
    art = root.xpath('.//article')[0]
    art.set('class', 'ag-site-card')
    for img in art.xpath('./img'):
        img.set('class', 'ag-site-card-image')
    content = art.xpath('./div[not(@aria-hidden="true")]')
    if content:
        content[0].set('class', 'ag-site-card-content')
    ph = art.xpath('./div[@aria-hidden="true"]')
    if ph:
        ph[0].set('class', 'ag-site-news-placeholder')
    for t in art.xpath('.//time'):
        p = t.getparent()
        if p is not None and p.tag == 'p':
            p.set('class', 'ag-site-kicker')
    for h in art.xpath('.//h2'):
        h.set('class', 'ag-site-card-title')
        for span in h.xpath('.//span'):
            span.set('class', 'ag-site-badge')
    for p in art.xpath('./div//p'):
        if not p.get('class'):
            p.set('class', 'ag-site-card-copy')
    for a in art.xpath('.//a'):
        if not a.get('class') and not a.xpath('ancestor::h2'):
            a.set('class', 'ag-site-link')
    source = record['source_url']
    if not source.startswith('https://'):
        raise ValueError('HTTPS source link required')
    container = content[0] if content else art
    if source in art.xpath('.//a/@href'):
        return tree.tostring(art, encoding='unicode', method='html')  # the card already links to its source
    p = tree.fragment_fromstring(f'<p class="ag-site-source"><a class="ag-site-link" href="{esc(source)}" target="_blank" rel="noopener noreferrer">Source</a></p>')
    container.append(p)
    return tree.tostring(art, encoding='unicode', method='html')


def build_news():
    items = yaml.safe_load((ROOT / 'data/news.yaml').read_text())
    cards = []
    for r in items:
        if not r.get('publish', True):
            continue
        if not r.get('source_url') or not r.get('verified'):
            raise ValueError(f'Published News item lacks a verified source: {r["id"]}')
        when = re.search(r'datetime="([0-9-]+)"', r['template_html'])
        cards.append((when.group(1) if when else '0000', news_card(r)))
    cards = [c for _, c in sorted(cards, key=lambda x: x[0], reverse=True)]  # newest first
    module = ('<!-- AUTO:news:START -->\n<div class="ag-site-root ag-site-news">'
              '<h1 class="ag-site-title">News</h1><p class="ag-site-lede">Research highlights, people, group visits and community events.</p>'
              '<div class="ag-site-news-grid">' + ''.join(cards) + '</div></div>\n<!-- AUTO:news:END -->')
    return module, ''


# ---------------------------------------------------------------- publications
selected_source = yaml.safe_load((ROOT / 'data/selected_publications.yaml').read_text())


def initials_name(full_name):
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    return f'{parts[-1]}, ' + ' '.join(p[0].upper() + '.' for p in parts[:-1])


def citation_details(paper):
    volume = str(paper.get('volume') or '').strip()
    issue = str(paper.get('issue') or '').strip()
    number = str(paper.get('article_number') or paper.get('pages') or '').strip()
    if issue and volume:
        volume += f' ({issue})'
    return f'{volume}, {number}' if volume and number else (volume or number)


def current_matches(paper):
    if int(paper.get('year', 0)) < 2022:
        return []
    return [a for a in paper.get('authors', []) if norm(a) in member_aliases]


eligible = []
seen = set()
for paper in selected_source:
    if paper['doi'] in seen:
        raise ValueError(f'Duplicate selected DOI: {paper["doi"]}')
    seen.add(paper['doi'])
    if paper.get('area') not in AREA_ORDER:
        raise ValueError(f'Unknown research area: {paper.get("area")}')
    if paper.get('status') != 'verified':
        raise ValueError(f'Unverified selected citation: {paper["doi"]}')
    matches = current_matches(paper)
    if matches:
        eligible.append((paper, matches))


def render_selected_paper(paper):
    authors = []
    for author in paper['authors']:
        label = esc(initials_name(author))
        authors.append(f'<strong>{label}</strong>' if norm(author) in member_aliases else label)
    doi_url = 'https://doi.org/' + paper['doi']
    meta = [f'<span class="ag-site-citation">{esc(citation_details(paper))}</span>'] if citation_details(paper) else []
    meta.append(f'<a class="ag-site-paper-doi" href="{esc(doi_url)}" target="_blank" rel="noopener noreferrer">DOI</a>')
    if paper.get('open_access'):
        meta.append('<span class="ag-site-open-access">Open access</span>')
    return (f'<li class="ag-site-paper"><span class="ag-site-paper-year">{int(paper["year"])}</span>'
            f'<div class="ag-site-paper-body"><span class="ag-site-paper-journal">{esc(paper["journal"])}</span>'
            f'<h3 class="ag-site-paper-title">{paper["title"]}</h3><p class="ag-site-paper-authors">{"; ".join(authors)}</p>'
            f'<div class="ag-site-paper-meta">{" ".join(meta)}</div></div></li>')


def selected_block():
    area_html, jumps = [], []
    for area in AREA_ORDER:
        papers = sorted([p for p, _ in eligible if p['area'] == area], key=lambda p: p.get('publication_date', ''), reverse=True)
        if not papers:
            continue
        label = TAGS['areas'][area]['label']
        jumps.append(chip(f'#selected-{area}', label))
        area_html.append(f'<section class="ag-site-area" id="selected-{area}" aria-labelledby="selected-heading-{area}">'
                         f'<h3 class="ag-site-area-heading" id="selected-heading-{area}">{esc(label)}</h3>'
                         f'<a class="ag-site-area-link" href="{SITE}/research/#{area}">About this research area →</a>'
                         f'<ul>{"".join(render_selected_paper(p) for p in papers)}</ul></section>')
    return ('<!-- AUTO:selected:START --><section class="ag-site-selected" aria-labelledby="selected-heading">'
            '<header><span class="ag-site-eyebrow">Since 2022</span><h2 class="ag-site-selected-heading" id="selected-heading">Selected Publications</h2>'
            '<p class="ag-site-selected-lede">Recent work by current group members, organized by research area. Names in bold are current group members.</p></header>'
            f'<nav class="ag-site-jumps" aria-label="Research areas">{"".join(jumps)}</nav>' + ''.join(area_html) +
            '</section><!-- AUTO:selected:END -->')


def bold_members(rec):
    """Bold current members by full-name match on the Crossref author list (never by initials alone), 2022 onward."""
    authors = rec['authors_html'].split('; ')
    names = rec.get('crossref_authors') or []
    if rec['group'] == '1980s' or int(rec['group']) < 2022 or len(names) != len(authors):
        return rec['authors_html']
    return '; '.join(f'<strong>{a}</strong>' if norm(n) in member_aliases else a for a, n in zip(authors, names))


def build_publications():
    recs, report = pubdata.load()
    tagged = any(r['areas'] or r['materials'] or r['approaches'] for r in recs)
    facets = [('areas', 'Research area', TAGS['areas']), ('materials', 'Material', TAGS['materials']),
              ('approaches', 'Approach', TAGS['approaches']), ('applications', 'Application', TAGS['applications'])]
    css, targets, statuses, groups = [], [], [], []
    total = len(recs)

    def add_filter(tid, cls, label, n):
        targets.append(tid)
        css.append(filter_css('ag-site-publications', tid, f'.ag-site-pub:not(.{cls})', f'#{tid}'))
        css.append(f'.ag-site-root.ag-site-publications:has(#{tid}:target) .ag-site-year:not(:has(.{cls})){{display:none}}')
        statuses.append(f'<p class="ag-site-filter-status ag-site-status-{tid}">Showing {n} of {total} papers: {esc(label)}.'
                        f'<a class="{NOSCROLL}" href="#pubs-all">Show all</a></p>')

    if tagged:
        for facet, title, vocab in facets:
            counts = Counter(t for r in recs for t in r[facet])
            chips = []
            for slug, spec in vocab.items():
                if counts[slug] < 3:
                    continue
                tid = f'f-{slug}'
                add_filter(tid, f't-{slug}', spec['label'], counts[slug])
                chips.append(chip(f'#{tid}', spec['label'], counts[slug]))
            if chips:
                groups.append((facet, f'<div class="ag-site-filter-group"><span class="ag-site-filter-label">{title}</span>{"".join(chips)}</div>'))
    type_counts = Counter(r['type'] for r in recs)
    type_chips = []
    for slug in ('review', 'perspective'):
        if type_counts[slug] >= 1:
            tid = f'f-type-{slug}'
            label = TAGS['types'][slug]['label']
            add_filter(tid, f't-type-{slug}', label, type_counts[slug])
            type_chips.append(chip(f'#{tid}', label, type_counts[slug]))
    oa_count = sum(r['oa'] for r in recs)
    add_filter('f-oa', 't-oa', 'Open access', oa_count)
    type_chips.append(chip('#f-oa', 'Open access', oa_count))
    groups.append(('type', f'<div class="ag-site-filter-group"><span class="ag-site-filter-label">Type</span>{"".join(type_chips)}</div>'))
    jcounts = Counter(r['journal_group'] for r in recs if r['journal_group'])
    jchips = []
    for slug, label, _ in pubdata.JOURNAL_GROUPS:
        if jcounts[slug]:
            tid = f'f-j-{slug}'
            add_filter(tid, f't-j-{slug}', label, jcounts[slug])
            jchips.append(chip(f'#{tid}', label, jcounts[slug]))
    groups.append(('journal', f'<div class="ag-site-filter-group"><span class="ag-site-filter-label">Journal</span>{"".join(jchips)}</div>'))

    main_groups = [g for k, g in groups if k in ('areas', 'journal', 'type')]
    more_groups = [g for k, g in groups if k in ('materials', 'approaches', 'applications')]
    filters_html = ('<div class="ag-site-filters">'
                    f'<div class="ag-site-filter-group"><span class="ag-site-filter-label">Showing</span>{chip("#pubs-all", "All papers", total, " ag-site-chip-all")}</div>'
                    + ''.join(main_groups) +
                    (f'<details class="ag-site-filters-more"><summary>More filters: material, approach, application</summary>{"".join(more_groups)}</details>' if more_groups else '')
                    + '</div>')

    years = sorted({r['group'] for r in recs}, key=lambda y: 1980 if y == '1980s' else int(y), reverse=True)
    number = total
    year_html = []
    tag_label = {(f, s): spec['label'] for f, _, vocab in facets for s, spec in vocab.items()}
    for year in years:
        items = []
        for r in [x for x in recs if x['group'] == year]:
            classes = ['ag-site-pub'] + [f't-{t}' for f in ('areas', 'materials', 'approaches', 'applications') for t in r[f]]
            classes.append(f't-type-{r["type"]}')
            if r['oa']:
                classes.append('t-oa')
            if r['journal_group']:
                classes.append(f't-j-{r["journal_group"]}')
            title = r['title_html']
            title_html = f'<a href="{esc(r["url"])}" target="_blank" rel="noopener noreferrer">{title}</a>' if r['url'] else title
            cite = f'<i>{esc(r["journal"])}</i> <b>{esc(r["year"])}</b>' + (f', {esc(r["details"])}' if r['details'] else '') + '.'
            pills = []
            for t in r['areas']:
                pills.append(f'<a class="{NOSCROLL}" href="#f-{t}">{esc(tag_label[("areas", t)])}</a>')
            for f in ('materials', 'approaches'):
                for t in r[f]:
                    pills.append(f'<span>{esc(tag_label[(f, t)])}</span>')
            if r['type'] != 'article':
                pills.append(f'<span class="ag-site-pt-type">{esc(TAGS["types"][r["type"]]["label"])}</span>')
            if r['oa']:
                pills.append('<span class="ag-site-pt-oa">Open access</span>')
            tags_html = f'<p class="ag-site-pub-tags">{"".join(pills)}</p>' if pills else ''
            items.append(f'<li class="{" ".join(classes)}" id="{esc(r["id"])}"><span class="ag-site-pub-num">{number}</span>'
                         f'<div class="ag-site-pub-body"><h3 class="ag-site-pub-title">{title_html}</h3>'
                         f'<p class="ag-site-pub-authors">{bold_members(r)}</p>'
                         f'<p class="ag-site-pub-cite">{cite}</p>{tags_html}</div></li>')
            number -= 1
        year_html.append(f'<section class="ag-site-year" id="pub-{year}" aria-labelledby="pub-heading-{year}">'
                         f'<h2 class="ag-site-year-heading" id="pub-heading-{year}">{year}</h2><ol>{"".join(items)}</ol></section>')
    nav = '<nav class="ag-site-year-nav" aria-label="Publication years">' + ''.join(f'<a class="{NOSCROLL}" href="#pub-{y}">{y}</a>' for y in years) + '</nav>'
    target_html = '<span class="ag-site-target" id="pubs-all"></span>' + ''.join(f'<span class="ag-site-target" id="{t}"></span>' for t in targets)
    module = ('<!-- AUTO:publications:START -->\n<div id="alivisatos-publications" class="ag-site-root ag-site-publications">'
              '<h1 class="ag-site-title">Publications</h1>' + selected_block() +
              '<section aria-labelledby="all-publications"><h2 class="ag-site-section-title" id="all-publications">All publications</h2>'
              f'<p class="ag-site-lede">{total} papers since 1983, newest first. Choose a filter to narrow the list; each filter has its own link to share.</p>'
              + target_html + filters_html + ''.join(statuses) + nav + ''.join(year_html) + '</section>'
              '<p class="ag-site-back-top"><a class="et_smooth_scroll_disabled" href="#pubs-all">Back to filters ↑</a></p>'
              '</div>\n<!-- AUTO:publications:END -->')
    write_metadata_report(recs, report)
    return module, ''.join(css)


def write_metadata_report(recs, report):
    lines = ['# Publication metadata check', '',
             f'{len(recs)} papers. Citation fields from Crossref: {sum(r["source"] == "crossref" for r in recs)}. '
             f'Kept from the page text: {sum(r["source"] == "page" for r in recs)}.', '',
             '| id | year | DOI | issue | page title | Crossref title |', '|---|---|---|---|---|---|']
    for row in report:
        lines.append('| ' + ' | '.join(str(x).replace('|', '/') for x in row) + ' |')
    (ROOT / 'reports/publication_metadata.md').write_text('\n'.join(lines) + '\n')


# ---------------------------------------------------------------- home
def home_publication_card(paper):
    d = date.fromisoformat(paper['publication_date'])
    summary = paper.get('homepage_summary', '')
    return ('<article class="ag-site-home-paper">'
            f'<p class="ag-site-home-paper-date">{esc(paper["journal"])} · {d:%B} {d.day}, {d.year}</p>'
            f'<h3 class="ag-site-home-paper-title"><a href="https://doi.org/{esc(paper["doi"])}" target="_blank" rel="noopener noreferrer">{paper["title"]}</a></h3>'
            + (f'<p class="ag-site-home-copy">{esc(summary)}</p>' if summary else '') + '</article>')


def build_home():
    home_news = yaml.safe_load((ROOT / 'data/home.yaml').read_text())
    key_papers = {k['area']: k for k in (yaml.safe_load((ROOT / 'data/key_papers.yaml').read_text()) or [])} if (ROOT / 'data/key_papers.yaml').exists() else {}
    recs, _ = pubdata.load()
    counts = Counter(t for r in recs for t in r['areas'])
    latest = sorted((p for p, _ in eligible if p.get('publication_date')), key=lambda p: p['publication_date'], reverse=True)[:3]
    if len(latest) != 3:
        raise ValueError('Home Latest Publications requires three dated selected records')
    news_cards = []
    for item in home_news:
        if not item.get('source_url'):
            raise ValueError(f'Home Latest News item lacks a source: {item["id"]}')
        rendered = item['template_html'].replace('@@TITLE_HTML@@', item['title_html'])
        root = strip_styles(rendered)
        art = root.xpath('.//article')[0]
        for span in art.xpath('.//h3//span'):
            span.set('class', 'ag-site-badge')
        art.set('class', 'ag-site-home-paper')
        ps = art.xpath('./p')
        if ps:
            ps[0].set('class', 'ag-site-home-paper-date')
        for p in ps[1:]:
            p.set('class', 'ag-site-home-copy')
        for h in art.xpath('./h3'):
            h.set('class', 'ag-site-home-news-title')
        art.append(tree.fragment_fromstring(f'<p class="ag-site-source"><a class="ag-site-link" href="{esc(item["source_url"])}" target="_blank" rel="noopener noreferrer">Source</a></p>'))
        news_cards.append(tree.tostring(art, encoding='unicode', method='html'))
    areas = []
    for area in AREA_ORDER + ['art']:
        label = AREA_PAGE_LABEL.get(area, 'Art with Nanoparticles')
        links = [f'<a href="{SITE}/research/#{area}">Read more</a>']
        if counts.get(area, 0) >= 3:
            links.append(f'<a href="{SITE}/publications/#f-{area}">{counts[area]} papers →</a>')
        key = key_papers.get(area)
        key_html = ''
        if key:
            key_html = (f'<p class="ag-site-area-key"><span class="ag-site-area-key-label">Featured paper</span>'
                        f'<a href="https://doi.org/{esc(key["doi"])}" target="_blank" rel="noopener noreferrer">{key["title"]}</a> '
                        f'<i>{esc(key["journal"])}</i> {key["year"]}</p>')
        areas.append(f'<div class="ag-site-area-card"><h3><a href="{SITE}/research/#{area}">{esc(label)}</a></h3>{key_html}'
                     f'<p class="ag-site-area-links">{"".join(links)}</p></div>')
    module = ('<!-- AUTO:home-updates:START -->\n<div class="ag-site-root ag-site-home">'
              '<section class="ag-site-section" aria-labelledby="home-latest-publications"><h2 class="ag-site-section-title" id="home-latest-publications">Latest Publications</h2>'
              '<!-- AUTO:latest-publications:START --><div class="ag-site-home-grid">' + ''.join(home_publication_card(p) for p in latest) + '</div><!-- AUTO:latest-publications:END -->'
              f'<p class="ag-site-view-all"><a href="{SITE}/publications/">View all publications →</a></p></section>'
              '<section class="ag-site-section" aria-labelledby="home-research-areas"><h2 class="ag-site-section-title" id="home-research-areas">Explore Our Research</h2>'
              '<div class="ag-site-research-grid">' + ''.join(areas) + '</div></section>'
              '<section class="ag-site-section" aria-labelledby="home-latest-news"><h2 class="ag-site-section-title" id="home-latest-news">Latest News</h2>'
              '<div class="ag-site-home-grid">' + ''.join(news_cards) + '</div>'
              f'<p class="ag-site-view-all"><a href="{SITE}/news/">View all news →</a></p></section>'
              + contact_block('home-contact') + '</div>\n<!-- AUTO:home-updates:END -->')
    return module, ''


# ---------------------------------------------------------------- research (label corrections only)
def build_research_corrections():
    raw = (ROOT / 'build/research-content.before-c.raw').read_text()
    (ROOT / 'build/research-content.raw').write_text(replace_research_citations(raw))


# ---------------------------------------------------------------- output
def minify_css(css):
    css = re.sub(r'/\*[\s\S]*?\*/', '', css)
    css = re.sub(r'\s+', ' ', css)
    css = re.sub(r'\s*([{};,])\s*', r'\1', css)
    return css.replace(';}', '}').strip()


def validate_markers(fragment, name):
    stack = []
    for marker, kind in re.findall(r'<!--\s*AUTO:([^:]+):(START|END)\s*-->', fragment):
        if kind == 'START':
            stack.append(marker)
        elif not stack or stack.pop() != marker:
            raise ValueError(f'Unbalanced AUTO markers in {name}: {marker}')
    if stack:
        raise ValueError(f'Unclosed AUTO markers in {name}: {stack}')


def main():
    build_research_corrections()
    base_css = (ROOT / 'assets/site.css').read_text()
    pages = {'members': build_members(), 'alumni': build_alumni(), 'news': build_news(),
             'publications': build_publications(), 'home': build_home()}
    for name, (fragment, extra_css) in pages.items():
        validate_markers(fragment, name)
        marker = 'home-updates' if name == 'home' else name
        if fragment.count(f'<!-- AUTO:{marker}:START -->') != 1 or fragment.count(f'<!-- AUTO:{marker}:END -->') != 1:
            raise ValueError(f'Missing main AUTO marker in {name}')
        if re.search(r'sci[-.]?hub', fragment, re.I):
            raise ValueError('Unexpected non-publisher link')
        if '@@' in fragment:
            raise ValueError(f'Unresolved template variable in {name}')
        root = tree.fragment_fromstring(fragment, create_parent='div')
        if root.xpath('.//style|.//script|.//input'):
            raise ValueError(f'{name}: style, script and input elements are removed on save')
        css = minify_css(base_css + extra_css)
        if '>' in css or '</' in css:
            raise ValueError(f'{name}: CSS must not contain ">" (escaped on save)')
        (OUT / f'{name}.html').write_text(fragment)
        (OUT / f'{name}.css').write_text(css)
        preview = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                   f'<title>{name}</title><style>body{{margin:0;padding:24px 16px;font-family:"Open Sans",Arial,sans-serif;background:#fff}}{css}</style></head>'
                   f'<body>{fragment}</body></html>')
        (OUT / f'{name}-preview.html').write_text(preview)
        print(f'{name}: {len(fragment):,} chars HTML, {len(css):,} chars CSS')


if __name__ == '__main__':
    main()
